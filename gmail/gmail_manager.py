import base64
import email
import os
import re
import time
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from threading import Lock
from typing import List, Dict, Any, Optional
from auth.google_auth import google_auth
from googleapiclient.errors import HttpError
import ssl

# Configura timeout global para sockets (2 minutos)
socket.setdefaulttimeout(120.0)


class GmailManager:
    """Classe para gerenciar operações no Gmail"""
    
    def __init__(self):
        self.service = google_auth.get_gmail_service()
        self.max_retries = 3
        self.retry_delay = 2  # segundos
        self.timeout = 60  # timeout de 60 segundos
        self._service_lock = Lock()
        self._labels_cache = {
            'timestamp': 0.0,
            'list': [],
            'map': {}
        }
        self._labels_cache_ttl = 300  # 5 minutos
    
    def _retry_on_error(self, func, *args, **kwargs):
        """Executa função com retry em caso de erro SSL ou Timeout"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                return result
            except (ssl.SSLError, socket.timeout, TimeoutError, ConnectionError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Backoff exponencial
                    error_type = type(e).__name__
                    print(f"Erro {error_type} (tentativa {attempt + 1}/{self.max_retries}). Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou - retorna None ao invés de lançar exceção
                    print(f"⚠️  Erro persistente após {self.max_retries} tentativas: {error_type}")
                    return None
            except HttpError as e:
                last_error = e
                # Erros HTTP 5xx são temporários, fazemos retry
                if e.resp.status >= 500 and attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Erro HTTP {e.resp.status} (tentativa {attempt + 1}/{self.max_retries}). Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Erro HTTP persistente ou não recuperável
                    print(f"⚠️  Erro HTTP não recuperável: {e.resp.status}")
                    return None
            except Exception as e:
                # Outros erros críticos - loga mas não quebra o servidor
                print(f"⚠️  Erro inesperado em retry: {type(e).__name__}: {str(e)[:100]}")
                return None
        
        # Se chegou aqui, todas as tentativas falharam
        return None
    
    def get_gmail_service(self):
        """Retorna o serviço do Gmail"""
        with self._service_lock:
            if not self.service:
                self.service = google_auth.get_gmail_service()
            return self.service

    def _get_labels_cache(self, force: bool = False):
        """Retorna cache de labels (lista e mapa id->label) com refresh controlado."""
        current_time = time.time()
        cache_age = current_time - self._labels_cache['timestamp']
        if not force and self._labels_cache['list'] and cache_age < self._labels_cache_ttl:
            return self._labels_cache['list'], self._labels_cache['map']

        def _fetch_labels():
            service = self.get_gmail_service()
            with self._service_lock:
                results = service.users().labels().list(userId='me').execute()
            return results.get('labels', [])

        labels = self._retry_on_error(_fetch_labels) or []
        label_map = {label['id']: label for label in labels}
        self._labels_cache = {
            'timestamp': current_time,
            'list': labels,
            'map': label_map
        }
        return labels, label_map
    
    def list_messages(
        self,
        query: str = None,
        max_results: int = 10,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lista mensagens do Gmail com otimização e suporte a paginação."""
        try:
            if max_results <= 0:
                return {
                    'messages': [],
                    'next_page_token': None,
                    'estimated_total': 0
                }

            def _fetch_messages():
                service = self.get_gmail_service()
                _, label_map = self._get_labels_cache()

                search_query = query or "in:inbox"
                max_fetch = max(1, min(max_results, 100))

                list_kwargs = dict(
                    userId='me',
                    q=search_query,
                    maxResults=max_fetch
                )
                if page_token:
                    list_kwargs['pageToken'] = page_token

                with self._service_lock:
                    results = service.users().messages().list(**list_kwargs).execute()

                messages = results.get('messages', [])
                next_page_token = results.get('nextPageToken')
                total_estimate = results.get('resultSizeEstimate', len(messages))

                if not messages:
                    return {
                        'messages': [],
                        'next_page_token': next_page_token,
                        'estimated_total': total_estimate
                    }

                detailed_messages = []
                processed_ids = set()
                order_map = {msg['id']: idx for idx, msg in enumerate(messages)}

                def build_label_info(label_ids: List[str]) -> List[Dict[str, Any]]:
                    info = []
                    for label_id in label_ids:
                        label_meta = label_map.get(label_id, {})
                        color_data = label_meta.get('color', {})
                        info.append({
                            'id': label_id,
                            'name': label_meta.get('name', label_id),
                            'type': label_meta.get('type', 'system' if label_id.isupper() else 'user'),
                            'text_color': color_data.get('textColor'),
                            'background_color': color_data.get('backgroundColor')
                        })
                    return info

                def process_response(response: Dict[str, Any]):
                    try:
                        message_id = response.get('id')
                        if not message_id or message_id in processed_ids:
                            return

                        headers = response['payload'].get('headers', [])
                        subject = self._get_header_value(headers, 'Subject')
                        sender = self._get_header_value(headers, 'From')
                        date = self._get_header_value(headers, 'Date')
                        label_ids = response.get('labelIds', []) or []
                        labels_info = build_label_info(label_ids)

                        detailed_messages.append({
                            'id': message_id,
                            'subject': subject,
                            'sender': sender,
                            'date': date,
                            'snippet': response.get('snippet', ''),
                            'thread_id': response.get('threadId', ''),
                            'unread': 'UNREAD' in label_ids,
                            'label_ids': label_ids,
                            'labels': labels_info,
                            'starred': 'STARRED' in label_ids,
                            'important': 'IMPORTANT' in label_ids
                        })
                        processed_ids.add(message_id)
                    except Exception as e:
                        print(f"⚠️  Erro ao processar mensagem: {type(e).__name__}")

                def fetch_single(message_id: str) -> Optional[Dict[str, Any]]:
                    try:
                        with self._service_lock:
                            return service.users().messages().get(
                                userId='me',
                                id=message_id,
                                format='metadata',
                                metadataHeaders=['Subject', 'From', 'Date']
                            ).execute()
                    except HttpError as single_error:
                        if single_error.resp.status == 404:
                            print(f"⚠️  Mensagem {message_id} não encontrada no fallback (404).")
                            return None
                        raise

                batch_size = max_fetch
                for i in range(0, len(messages), batch_size):
                    batch = messages[i:i + batch_size]

                    def callback(request_id, response, exception):
                        if exception:
                            if isinstance(exception, HttpError) and exception.resp.status == 404:
                                print(f"⚠️  Mensagem {request_id} não encontrada (404). Pulando.")
                            else:
                                print(f"⚠️  Erro na mensagem {request_id}: {type(exception).__name__}")
                            return
                        process_response(response)

                    try:
                        with self._service_lock:
                            batch_request = service.new_batch_http_request(callback=callback)
                            for msg in batch:
                                batch_request.add(
                                    service.users().messages().get(
                                        userId='me',
                                        id=msg['id'],
                                        format='metadata',
                                        metadataHeaders=['Subject', 'From', 'Date']
                                    ),
                                    request_id=msg['id']
                                )
                            batch_request.execute(http=service._http)
                    except HttpError as batch_error:
                        if batch_error.resp.status == 404:
                            print("⚠️  Batch retornou 404. Tentando fallback individual para este lote.")
                            for msg in batch:
                                response = fetch_single(msg['id'])
                                if response:
                                    process_response(response)
                        else:
                            raise

                # Ordena resultados para manter a ordem original do Gmail
                detailed_messages.sort(key=lambda msg: order_map.get(msg['id'], 0))

                return {
                    'messages': detailed_messages[:max_fetch],
                    'next_page_token': next_page_token,
                    'estimated_total': total_estimate
                }

            result = self._retry_on_error(_fetch_messages)
            if not result:
                return {
                    'messages': [],
                    'next_page_token': None,
                    'estimated_total': 0
                }
            return result

        except Exception as e:
            print(f"Erro crítico ao listar mensagens: {type(e).__name__}: {str(e)[:100]}")
            return {
                'messages': [],
                'next_page_token': None,
                'estimated_total': 0
            }
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Obtém uma mensagem específica"""
        try:
            with self._service_lock:
                message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
            
            headers = message['payload'].get('headers', [])
            
            return {
                'id': message['id'],
                'subject': self._get_header_value(headers, 'Subject'),
                'sender': self._get_header_value(headers, 'From'),
                'recipient': self._get_header_value(headers, 'To'),
                'date': self._get_header_value(headers, 'Date'),
                'body': self._get_message_body(message['payload']),
                'attachments': self._get_attachments(message['payload'])
            }
            
        except Exception as e:
            print(f"Erro ao obter mensagem: {e}")
            return {}
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = None, bcc: str = None, 
                   attachments: List[str] = None) -> bool:
        """Envia um email"""
        try:
            # Criar mensagem
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Adicionar corpo do email
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Adicionar anexos se houver
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(message, file_path)
                    else:
                        print(f"Aviso: Arquivo {file_path} não encontrado")
            
            # Codificar mensagem
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Enviar email
            with self._service_lock:
                send_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            
            print(f"Email enviado com sucesso! ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False
    
    def send_html_email(self, to: str, subject: str, html_body: str, 
                       cc: str = None, bcc: str = None) -> bool:
        """Envia um email HTML"""
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Adicionar versão HTML
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # Codificar e enviar
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            with self._service_lock:
                send_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            
            print(f"Email HTML enviado com sucesso! ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email HTML: {e}")
            return False
    
    def reply_to_message(self, message_id: str, reply_text: str) -> bool:
        """Responde a uma mensagem"""
        try:
            # Obter mensagem original
            with self._service_lock:
                original_message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
            
            headers = original_message['payload'].get('headers', [])
            original_subject = self._get_header_value(headers, 'Subject')
            original_sender = self._get_header_value(headers, 'From')
            
            # Criar resposta
            reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
            
            message = MIMEText(reply_text, 'plain', 'utf-8')
            message['to'] = original_sender
            message['subject'] = reply_subject
            message['In-Reply-To'] = original_message['id']
            
            # Codificar e enviar
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            with self._service_lock:
                send_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            
            print(f"Resposta enviada com sucesso! ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"Erro ao responder mensagem: {e}")
            return False
    
    def forward_message(self, message_id: str, to: str, forward_text: str = None) -> bool:
        """Encaminha uma mensagem"""
        try:
            # Obter mensagem original
            with self._service_lock:
                original_message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
            
            headers = original_message['payload'].get('headers', [])
            original_subject = self._get_header_value(headers, 'Subject')
            
            # Criar encaminhamento
            forward_subject = f"Fwd: {original_subject}" if not original_subject.startswith('Fwd:') else original_subject
            
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = forward_subject
            
            # Adicionar texto do encaminhamento
            if forward_text:
                message.attach(MIMEText(forward_text, 'plain', 'utf-8'))
            
            # Adicionar mensagem original
            original_body = self._get_message_body(original_message['payload'])
            message.attach(MIMEText(f"\n\n--- Mensagem Original ---\n{original_body}", 'plain', 'utf-8'))
            
            # Codificar e enviar
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            with self._service_lock:
                send_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            
            print(f"Mensagem encaminhada com sucesso! ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"Erro ao encaminhar mensagem: {e}")
            return False
    
    def delete_message(self, message_id: str) -> bool:
        """Exclui uma mensagem"""
        try:
            with self._service_lock:
                self.service.users().messages().delete(
                    userId='me',
                    id=message_id
                ).execute()
            
            print("Mensagem excluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao excluir mensagem: {e}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """Marca mensagem como lida"""
        try:
            with self._service_lock:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            
            print("Mensagem marcada como lida!")
            return True
            
        except Exception as e:
            print(f"Erro ao marcar como lida: {e}")
            return False
    
    def mark_as_unread(self, message_id: str) -> bool:
        """Marca mensagem como não lida"""
        try:
            with self._service_lock:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'addLabelIds': ['UNREAD']}
                ).execute()
            
            print("Mensagem marcada como não lida!")
            return True
            
        except Exception as e:
            print(f"Erro ao marcar como não lida: {e}")
            return False
    
    def add_label(self, message_id: str, label_name: str) -> bool:
        """Adiciona label a uma mensagem"""
        try:
            # Obter ou criar label
            label_id = self._get_or_create_label(label_name)

            with self._service_lock:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
            
            print(f"Label '{label_name}' adicionada à mensagem!")
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar label: {e}")
            return False
    
    def remove_label(self, message_id: str, label_name: str) -> bool:
        """Remove label de uma mensagem"""
        try:
            # Obter ID do label
            label_id = self._get_label_id(label_name)
            
            if label_id:
                with self._service_lock:
                    self.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={'removeLabelIds': [label_id]}
                    ).execute()
                
                print(f"Label '{label_name}' removida da mensagem!")
                return True
            else:
                print(f"Label '{label_name}' não encontrada!")
                return False
                
        except Exception as e:
            print(f"Erro ao remover label: {e}")
            return False
    
    def _batch_modify(self, message_ids: List[str], add_labels: Optional[List[str]] = None,
                      remove_labels: Optional[List[str]] = None) -> bool:
        """Executa operação batchModify no Gmail."""
        if not message_ids:
            return True
        try:
            body: Dict[str, Any] = {'ids': message_ids}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels
            with self._service_lock:
                self.service.users().messages().batchModify(
                    userId='me',
                    body=body
                ).execute()
            return True
        except Exception as e:
            print(f"⚠️  Erro no batchModify: {type(e).__name__}: {str(e)[:200]}")
            return False

    def archive_messages(self, message_ids: List[str]) -> bool:
        """Remove a label INBOX de múltiplas mensagens (arquivar)."""
        return self._batch_modify(message_ids, remove_labels=['INBOX'])

    def mark_messages_read(self, message_ids: List[str]) -> bool:
        """Marca múltiplas mensagens como lidas."""
        return self._batch_modify(message_ids, remove_labels=['UNREAD'])

    def mark_messages_unread(self, message_ids: List[str]) -> bool:
        """Marca múltiplas mensagens como não lidas."""
        return self._batch_modify(message_ids, add_labels=['UNREAD'])

    def delete_messages(self, message_ids: List[str]) -> bool:
        """Exclui múltiplas mensagens."""
        if not message_ids:
            return True
        try:
            with self._service_lock:
                self.service.users().messages().batchDelete(
                    userId='me',
                    body={'ids': message_ids}
                ).execute()
            return True
        except Exception as e:
            print(f"⚠️  Erro no batchDelete: {type(e).__name__}: {str(e)[:200]}")
            return False
    
    def search_messages(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca mensagens com query específica"""
        result = self.list_messages(query, max_results)
        return result.get('messages', [])
    
    def get_unread_count(self) -> int:
        """Obtém contagem de mensagens não lidas"""
        try:
            def _get_count():
                with self._service_lock:
                    results = self.service.users().messages().list(
                        userId='me',
                        q='is:unread',
                        maxResults=1
                    ).execute()
                    return results.get('resultSizeEstimate', 0)
            
            result = self._retry_on_error(_get_count)
            # Se o retry retornou None, retorna 0
            return result if result is not None else 0
            
        except Exception as e:
            print(f"⚠️  Erro ao obter contagem de não lidas: {type(e).__name__}")
            return 0
    
    def get_labels(self) -> List[Dict[str, Any]]:
        """Obtém lista de labels"""
        try:
            labels_list, _ = self._get_labels_cache()
            formatted = []
            for label in labels_list:
                formatted.append({
                    'id': label.get('id'),
                    'name': label.get('name'),
                    'type': label.get('type', 'system' if (label.get('id') or '').isupper() else 'user'),
                    'messages_total': label.get('messagesTotal'),
                    'messages_unread': label.get('messagesUnread'),
                    'color': label.get('color', {})
                })
            return formatted
            
        except Exception as e:
            print(f"⚠️  Erro ao obter labels: {type(e).__name__}")
            return []
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Obtém o perfil do usuário (total de mensagens, threads, etc.) com retries."""
        try:
            def _fetch_profile():
                with self._service_lock:
                    return self.service.users().getProfile(userId='me').execute()
            
            # Usa a nossa função de retry robusta
            result = self._retry_on_error(_fetch_profile)
            return result  # Retorna o perfil ou None se falhar
            
        except Exception as e:
            print(f"⚠️  Erro ao obter perfil do Gmail: {type(e).__name__}")
            return None
    
    def create_label(self, name: str) -> Optional[str]:
        """Cria um novo label"""
        try:
            label = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }

            with self._service_lock:
                created_label = self.service.users().labels().create(
                    userId='me',
                    body=label
                ).execute()
            # Invalida cache para garantir que nova label apareça
            self._labels_cache['timestamp'] = 0.0

            print(f"Label '{name}' criado com sucesso!")
            return created_label['id']
            
        except Exception as e:
            print(f"Erro ao criar label: {e}")
            return None
    
    def download_attachment(self, message_id: str, attachment_id: str, 
                          filename: str = None) -> bool:
        """Baixa um anexo"""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            
            if not filename:
                filename = f"attachment_{attachment_id}"
            
            with open(filename, 'wb') as f:
                f.write(file_data)
            
            print(f"Anexo baixado: {filename}")
            return True
            
        except Exception as e:
            print(f"Erro ao baixar anexo: {e}")
            return False
    
    # Métodos auxiliares
    def _get_header_value(self, headers: List[Dict], name: str) -> str:
        """Obtém valor de um header"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extrai o corpo da mensagem (text/plain e text/html)"""
        body_plain = ""
        body_html = ""

        def extract_body_from_part(part):
            """Extrai corpo de uma parte da mensagem"""
            nonlocal body_plain, body_html

            mime_type = part.get('mimeType', '')

            # Se tem subpartes, processa recursivamente
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_body_from_part(subpart)
            else:
                # Extrai o conteúdo
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        if mime_type == 'text/plain':
                            body_plain += decoded
                        elif mime_type == 'text/html':
                            body_html += decoded
                    except Exception as e:
                        print(f"Erro ao decodificar parte da mensagem: {e}")

        # Processa o payload
        extract_body_from_part(payload)

        # Retorna plain text se disponível, senão HTML, senão vazio
        return body_plain if body_plain else body_html if body_html else "Corpo da mensagem não disponível"
    
    def _get_attachments(self, payload: Dict) -> List[Dict[str, Any]]:
        """Extrai informações dos anexos"""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['filename']:
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachmentId': part['body'].get('attachmentId', '')
                    })
        
        return attachments
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Adiciona anexo à mensagem"""
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(file_path)}'
        )
        message.attach(part)
    
    def _get_label_id(self, label_name: str) -> Optional[str]:
        """Obtém ID de um label pelo nome"""
        labels = self.get_labels()
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        return None
    
    def _get_or_create_label(self, label_name: str) -> str:
        """Obtém ou cria um label"""
        label_id = self._get_label_id(label_name)
        if not label_id:
            label_id = self.create_label(label_name)
        return label_id
