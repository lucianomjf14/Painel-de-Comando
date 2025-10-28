import base64
import email
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from auth.google_auth import google_auth


class GmailManager:
    """Classe para gerenciar operações no Gmail"""
    
    def __init__(self):
        self.service = google_auth.get_gmail_service()
    
    def get_gmail_service(self):
        """Retorna o serviço do Gmail"""
        if not self.service:
            self.service = google_auth.get_gmail_service()
        return self.service
    
    def list_messages(self, query: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Lista mensagens do Gmail"""
        try:
            # Se não há query, busca todas as mensagens
            if not query:
                query = "in:inbox"
            
            # Buscar mensagens
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("Nenhuma mensagem encontrada.")
                return []
            
            # Obter detalhes das mensagens
            detailed_messages = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extrair informações da mensagem
                headers = msg['payload'].get('headers', [])
                subject = self._get_header_value(headers, 'Subject')
                sender = self._get_header_value(headers, 'From')
                date = self._get_header_value(headers, 'Date')
                
                detailed_messages.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': msg.get('snippet', ''),
                    'thread_id': msg.get('threadId', '')
                })
            
            return detailed_messages
            
        except Exception as e:
            print(f"Erro ao listar mensagens: {e}")
            return []
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Obtém uma mensagem específica"""
        try:
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
    
    def search_messages(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca mensagens com query específica"""
        return self.list_messages(query, max_results)
    
    def get_unread_count(self) -> int:
        """Obtém contagem de mensagens não lidas"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=1
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
            
        except Exception as e:
            print(f"Erro ao obter contagem de não lidas: {e}")
            return 0
    
    def get_labels(self) -> List[Dict[str, Any]]:
        """Obtém lista de labels"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            return [{'id': label['id'], 'name': label['name']} for label in labels]
            
        except Exception as e:
            print(f"Erro ao obter labels: {e}")
            return []
    
    def create_label(self, name: str) -> Optional[str]:
        """Cria um novo label"""
        try:
            label = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label
            ).execute()
            
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
        """Extrai o corpo da mensagem"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
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
