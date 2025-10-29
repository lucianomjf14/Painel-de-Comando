import os
import io
import time
import ssl
import socket
from typing import List, Dict, Any, Optional
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
from auth.google_auth import google_auth
from config import MAX_RESULTS

# Configura timeout global para sockets (2 minutos)
socket.setdefaulttimeout(120.0)


class GoogleDriveManager:
    """Classe para gerenciar operações no Google Drive"""
    
    def __init__(self):
        self.service = google_auth.get_drive_service()
        self.max_retries = 3
        self.retry_delay = 2  # segundos (aumentado para maior backoff)
        self.timeout = 60  # timeout em segundos
    
    def _retry_on_error(self, func, *args, **kwargs):
        """Executa função com retry em caso de erro SSL, timeout ou HTTP 5xx"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (ssl.SSLError, socket.timeout, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Backoff exponencial
                    error_type = type(e).__name__
                    print(f"Erro {error_type} (tentativa {attempt + 1}/{self.max_retries}). Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    print(f"Erro persistente após {self.max_retries} tentativas: {e}")
                    raise
            except HttpError as e:
                # Retry apenas para erros 5xx (servidor)
                if e.resp.status >= 500 and attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Erro HTTP {e.resp.status} (tentativa {attempt + 1}/{self.max_retries}). Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                # Outros erros não fazem retry
                raise
    
    def list_files(self, query: str = None, max_results: int = MAX_RESULTS) -> List[Dict[str, Any]]:
        """Lista arquivos do Google Drive"""
        try:
            # Query padrão para listar todos os arquivos
            if not query:
                query = "trashed=false"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                print("Nenhum arquivo encontrado.")
                return []
            
            return files
            
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []
    
    def search_files(self, name: str, mime_type: str = None) -> List[Dict[str, Any]]:
        """Busca arquivos por nome"""
        try:
            query = f"name contains '{name}' and trashed=false"
            
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            return self.list_files(query)
            
        except Exception as e:
            print(f"Erro ao buscar arquivos: {e}")
            return []
    
    def upload_file(self, file_path: str, folder_id: str = None, name: str = None) -> Optional[str]:
        """Faz upload de um arquivo para o Google Drive"""
        try:
            if not os.path.exists(file_path):
                print(f"Arquivo não encontrado: {file_path}")
                return None
            
            file_name = name or os.path.basename(file_path)
            
            # Metadados do arquivo
            file_metadata = {
                'name': file_name
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Upload do arquivo
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            print(f"Arquivo '{file_name}' enviado com sucesso!")
            print(f"ID: {file_id}")
            print(f"URL: https://drive.google.com/file/d/{file_id}/view")
            
            return file_id
            
        except Exception as e:
            print(f"Erro ao fazer upload do arquivo: {e}")
            return None
    
    def download_file(self, file_id: str, output_path: str = None) -> bool:
        """Faz download de um arquivo do Google Drive"""
        try:
            # Obtém informações do arquivo
            file_info = self.service.files().get(fileId=file_id).execute()
            file_name = file_info.get('name')
            
            if not output_path:
                output_path = file_name
            
            # Faz o download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% concluído.")
            
            # Salva o arquivo
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            print(f"Arquivo '{file_name}' baixado com sucesso para '{output_path}'!")
            return True
            
        except Exception as e:
            print(f"Erro ao fazer download do arquivo: {e}")
            return False
    
    def create_folder(self, name: str, parent_folder_id: str = None) -> Optional[str]:
        """Cria uma nova pasta no Google Drive"""
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            print(f"Pasta '{name}' criada com sucesso!")
            print(f"ID: {folder_id}")
            print(f"URL: https://drive.google.com/drive/folders/{folder_id}")
            
            return folder_id
            
        except Exception as e:
            print(f"Erro ao criar pasta: {e}")
            return None
    
    def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """Exclui um arquivo do Google Drive"""
        try:
            if permanent:
                # Exclusão permanente
                self.service.files().delete(fileId=file_id).execute()
                print("Arquivo excluído permanentemente!")
            else:
                # Move para lixeira
                self.service.files().update(
                    fileId=file_id,
                    body={'trashed': True}
                ).execute()
                print("Arquivo movido para lixeira!")
            
            return True
            
        except Exception as e:
            print(f"Erro ao excluir arquivo: {e}")
            return False
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Obtém informações detalhadas de um arquivo"""
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink"
            ).execute()
            
            return file_info
            
        except Exception as e:
            print(f"Erro ao obter informações do arquivo: {e}")
            return {}
    
    def copy_file(self, file_id: str, new_name: str = None, folder_id: str = None) -> Optional[str]:
        """Cria uma cópia de um arquivo"""
        try:
            copied_file = {'name': new_name} if new_name else {}
            
            if folder_id:
                copied_file['parents'] = [folder_id]
            
            file = self.service.files().copy(
                fileId=file_id,
                body=copied_file
            ).execute()
            
            new_file_id = file.get('id')
            print(f"Arquivo copiado com sucesso!")
            print(f"Novo ID: {new_file_id}")
            
            return new_file_id
            
        except Exception as e:
            print(f"Erro ao copiar arquivo: {e}")
            return None
    
    def move_file(self, file_id: str, folder_id: str) -> bool:
        """Move um arquivo para outra pasta"""
        try:
            # Obtém informações do arquivo atual
            file_info = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file_info.get('parents'))
            
            # Move o arquivo
            self.service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            print("Arquivo movido com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao mover arquivo: {e}")
            return False
