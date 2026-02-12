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
    """Classe para gerenciar operações no Google Drive com suporte a drives compartilhados"""
    
    def __init__(self):
        self.service = google_auth.get_drive_service()
        self.max_retries = 3
        self.retry_delay = 2
        self.timeout = 60

    
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
    
    def list_files(self, query: str = None, max_results: int = MAX_RESULTS, include_shared: bool = True) -> List[Dict[str, Any]]:
        """Lista arquivos do Google Drive incluindo arquivos compartilhados comigo"""
        try:
            # Query padrão para listar todos os arquivos
            if not query:
                query = "trashed=false"
            
            # Parâmetros base
            params = {
                'q': query,
                'pageSize': max_results,
                'fields': "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, shared, sharedWithMeTime, ownedByMe, owners)"
            }
            
            # Adiciona suporte para arquivos compartilhados e drives compartilhados
            if include_shared:
                params['corpora'] = 'allDrives'
                params['includeItemsFromAllDrives'] = True
                params['supportsAllDrives'] = True
            
            results = self.service.files().list(**params).execute()
            
            files = results.get('files', [])
            
            if not files:
                print("Nenhum arquivo encontrado.")
                return []
            
            return files
            
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []
    
    def list_shared_drives(self) -> List[Dict[str, Any]]:
        """Lista os Drives compartilhados (Drives de equipe)"""
        try:
            if not self.service:
                print("❌ Serviço do Drive não inicializado")
                return []
            
            print("🔍 Buscando Drives compartilhados...")
            results = self.service.drives().list(
                pageSize=100,
                fields="drives(id, name, createdTime, capabilities)"
            ).execute()
            
            drives = results.get('drives', [])
            
            if not drives:
                print("⚠️ Nenhum Drive compartilhado encontrado.")
                print("   Verifique se você tem acesso a algum Drive de equipe")
                return []
            
            print(f"✅ {len(drives)} Drive(s) compartilhado(s) encontrado(s):")
            for drive in drives:
                print(f"   📁 {drive['name']} (ID: {drive['id']})")
            return drives
            
        except Exception as e:
            print(f"❌ Erro ao listar Drives compartilhados: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def list_files_in_shared_drive(self, drive_id: str, parent_id: str = None, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Lista arquivos de um Drive compartilhado
        Se parent_id for None, retorna estrutura completa (build_folder_tree)
        Se parent_id for fornecido, retorna apenas filhos daquela pasta
        """
        try:
            # Se parent_id foi fornecido, lista apenas aquela pasta
            if parent_id:
                all_files = []
                page_token = None
                
                print(f"🔍 Listando pasta {parent_id}...")
                
                while True:
                    params = {
                        'driveId': drive_id,
                        'corpora': 'drive',
                        'includeItemsFromAllDrives': True,
                        'supportsAllDrives': True,
                        'pageSize': min(max_results, 1000),
                        'fields': "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, shared, driveId, webViewLink, iconLink, fileExtension)",
                        'q': f"'{parent_id}' in parents and trashed=false"
                    }
                    
                    if page_token:
                        params['pageToken'] = page_token
                    
                    results = self.service.files().list(**params).execute()
                    files = results.get('files', [])
                    all_files.extend(files)
                    
                    page_token = results.get('nextPageToken')
                    if not page_token or len(all_files) >= max_results:
                        break
                
                # Função para extrair número do início do nome
                def extract_number(name):
                    import re
                    match = re.match(r'^(\d+(?:\.\d+)?)', name)
                    return float(match.group(1)) if match else float('inf')
                
                # Separa pastas e arquivos
                folders = [f for f in all_files if f['mimeType'] == 'application/vnd.google-apps.folder']
                regular_files = [f for f in all_files if f['mimeType'] != 'application/vnd.google-apps.folder']
                
                # Ordena por número primeiro, depois alfabeticamente
                folders.sort(key=lambda x: (extract_number(x['name']), x['name']))
                regular_files.sort(key=lambda x: (extract_number(x['name']), x['name']))
                
                return {
                    'folders': folders,
                    'files': regular_files,
                    'total': len(all_files)
                }
            
            # Se parent_id é None, busca arquivos NA RAIZ do drive compartilhado
            # Em drives compartilhados, a raiz tem um ID específico que é o próprio driveId
            all_files = []
            page_token = None
            
            print(f"🔍 Buscando arquivos NA RAIZ do Drive {drive_id}...")
            
            while True:
                params = {
                    'driveId': drive_id,
                    'corpora': 'drive',
                    'includeItemsFromAllDrives': True,
                    'supportsAllDrives': True,
                    'pageSize': min(max_results, 1000),
                    'fields': "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, shared, driveId, webViewLink, iconLink)",
                    # Busca arquivos cuja pasta pai é a raiz do drive
                    'q': f"'{drive_id}' in parents and trashed=false"
                }
                
                if page_token:
                    params['pageToken'] = page_token
                
                results = self.service.files().list(**params).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                print(f"   📄 {len(files)} arquivos encontrados na raiz (total: {len(all_files)})")
                
                page_token = results.get('nextPageToken')
                if not page_token or len(all_files) >= max_results:
                    break
            
            print(f"✅ Total: {len(all_files)} itens na raiz do Drive compartilhado")
            
            # Separa pastas e arquivos
            folders = [f for f in all_files if f['mimeType'] == 'application/vnd.google-apps.folder']
            regular_files = [f for f in all_files if f['mimeType'] != 'application/vnd.google-apps.folder']
            
            # Função para extrair número do início do nome
            def extract_number(name):
                import re
                match = re.match(r'^(\d+(?:\.\d+)?)', name)
                return float(match.group(1)) if match else float('inf')
            
            # Ordena por número primeiro, depois alfabeticamente
            folders.sort(key=lambda x: (extract_number(x['name']), x['name']))
            regular_files.sort(key=lambda x: (extract_number(x['name']), x['name']))
            
            print(f"   📁 Pastas: {len(folders)}")
            print(f"   📄 Arquivos: {len(regular_files)}")
            
            return {
                'folders': folders,
                'files': regular_files,
                'total': len(all_files)
            }
            
        except Exception as e:
            print(f"❌ Erro ao listar arquivos do Drive compartilhado: {e}")
            return {'folders': [], 'files': [], 'total': 0}
    
    def build_folder_tree(self, drive_id: str) -> Dict[str, Any]:
        """Constrói árvore completa de pastas e arquivos de um Drive compartilhado"""
        try:
            print(f"\n{'='*60}")
            print(f"🌳 CONSTRUINDO ÁRVORE COMPLETA DO DRIVE")
            print(f"{'='*60}\n")
            
            # Lista TODOS os arquivos
            all_items = self.list_files_in_shared_drive(drive_id, max_results=10000)
            
            if not all_items:
                return {'folders': [], 'files': [], 'total_folders': 0, 'total_files': 0}
            
            # Separa pastas e arquivos
            folders = [item for item in all_items if item['mimeType'] == 'application/vnd.google-apps.folder']
            files = [item for item in all_items if item['mimeType'] != 'application/vnd.google-apps.folder']
            
            print(f"📊 ESTATÍSTICAS:")
            print(f"   📁 Pastas: {len(folders)}")
            print(f"   📄 Arquivos: {len(files)}")
            print(f"   📦 Total de itens: {len(all_items)}")
            
            # Cria mapeamento de ID para item
            items_map = {item['id']: item for item in all_items}
            
            # Adiciona lista de filhos em cada pasta
            for folder in folders:
                folder['children'] = []
                folder['files'] = []
                folder['subfolders'] = []
            
            # Identifica itens raiz (sem parent ou parent não está na lista)
            root_items = []
            
            for item in all_items:
                parents = item.get('parents', [])
                
                if not parents:
                    # Item na raiz
                    root_items.append(item)
                else:
                    # Adiciona aos pais
                    parent_id = parents[0]
                    if parent_id in items_map:
                        parent = items_map[parent_id]
                        if 'children' in parent:
                            parent['children'].append(item)
                            if item['mimeType'] == 'application/vnd.google-apps.folder':
                                parent['subfolders'].append(item)
                            else:
                                parent['files'].append(item)
                    else:
                        # Parent não encontrado, considera como raiz
                        root_items.append(item)
            
            # Separa raiz em pastas e arquivos
            root_folders = [item for item in root_items if item['mimeType'] == 'application/vnd.google-apps.folder']
            root_files = [item for item in root_items if item['mimeType'] != 'application/vnd.google-apps.folder']
            
            print(f"\n📂 ESTRUTURA RAIZ:")
            print(f"   📁 Pastas na raiz: {len(root_folders)}")
            print(f"   📄 Arquivos na raiz: {len(root_files)}")
            
            # Calcula estatísticas recursivas
            def count_items(folder):
                total = len(folder.get('files', []))
                for subfolder in folder.get('subfolders', []):
                    total += count_items(subfolder)
                return total
            
            # Adiciona contadores em cada pasta
            for folder in folders:
                folder['total_files_recursive'] = count_items(folder)
                folder['total_subfolders_recursive'] = len(folder.get('subfolders', []))
            
            return {
                'folders': root_folders,
                'files': root_files,
                'all_items': all_items,
                'total_folders': len(folders),
                'total_files': len(files),
                'total_items': len(all_items),
                'items_map': items_map
            }
            
        except Exception as e:
            print(f"❌ Erro ao construir árvore: {e}")
            import traceback
            traceback.print_exc()
            return {'folders': [], 'files': [], 'total_folders': 0, 'total_files': 0}
    
    def get_folder_stats(self, drive_id: str, folder_id: Optional[str] = None) -> Dict[str, int]:
        """Retorna estatísticas de uma pasta ou drive"""
        try:
            if folder_id:
                # Estatísticas de pasta específica
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                # Estatísticas do drive inteiro
                query = "trashed=false"
            
            all_items = []
            page_token = None
            
            while True:
                params = {
                    'driveId': drive_id,
                    'corpora': 'drive',
                    'includeItemsFromAllDrives': True,
                    'supportsAllDrives': True,
                    'q': query,
                    'pageSize': 1000,
                    'fields': 'nextPageToken, files(id, mimeType, size)'
                }
                
                if page_token:
                    params['pageToken'] = page_token
                
                results = self.service.files().list(**params).execute()
                items = results.get('files', [])
                all_items.extend(items)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            total_folders = sum(1 for item in all_items if item['mimeType'] == 'application/vnd.google-apps.folder')
            total_files = len(all_items) - total_folders
            total_size = sum(int(item.get('size', 0)) for item in all_items if item.get('size'))
            
            return {
                'total_folders': total_folders,
                'total_files': total_files,
                'total_size': total_size,
                'total_items': len(all_items)
            }
        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {'total_folders': 0, 'total_files': 0, 'total_size': 0, 'total_items': 0}
    
    def search_in_drive(self, drive_id: str, query_text: str) -> List[Dict[str, Any]]:
        """Busca arquivos em um drive compartilhado"""
        try:
            query = f"name contains '{query_text}' and trashed=false"
            
            response = self.service.files().list(
                driveId=drive_id,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                q=query,
                pageSize=50,
                fields="files(id, name, mimeType, size, parents, webViewLink, iconLink)",
                orderBy="name"
            ).execute()
            
            return response.get('files', [])
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def list_shared_with_me(self, max_results: int = MAX_RESULTS) -> List[Dict[str, Any]]:
        """Lista apenas arquivos compartilhados comigo"""
        try:
            query = "sharedWithMe=true and trashed=false"
            return self.list_files(query, max_results, include_shared=True)
        except Exception as e:
            print(f"Erro ao listar arquivos compartilhados: {e}")
            return []
    
    def get_folder_contents(self, drive_id: str, folder_id: str = None) -> Dict[str, Any]:
        """Lista apenas o conteúdo direto de uma pasta (otimizado para lazy loading)"""
        try:
            # Query para listar itens de uma pasta específica ou raiz
            if folder_id:
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                # Raiz do Drive (sem parent)
                query = "trashed=false"
            
            print(f"📂 Listando conteúdo da pasta {folder_id or 'raiz'}...")
            
            results = self.service.files().list(
                driveId=drive_id,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                q=query,
                pageSize=1000,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            
            # Separa pastas e arquivos
            folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
            files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
            
            # Se estamos na raiz, filtra apenas itens sem parent ou com parent = drive_id
            if not folder_id:
                folders = [f for f in folders if not f.get('parents') or drive_id in f.get('parents', [])]
                files = [f for f in files if not f.get('parents') or drive_id in f.get('parents', [])]
            
            print(f"✅ {len(folders)} pastas, {len(files)} arquivos")
            
            return {
                'folders': folders,
                'files': files,
                'total_folders': len(folders),
                'total_files': len(files)
            }
            
        except Exception as e:
            print(f"❌ Erro ao listar pasta: {e}")
            return {'folders': [], 'files': [], 'total_folders': 0, 'total_files': 0}
    
    def get_drive_stats(self, drive_id: str) -> Dict[str, Any]:
        """Obtém estatísticas rápidas do Drive (apenas contadores)"""
        try:
            print(f"📊 Calculando estatísticas do Drive {drive_id}...")
            
            # Conta apenas, sem trazer todos os dados
            results = self.service.files().list(
                driveId=drive_id,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                q='trashed=false',
                pageSize=1000,
                fields="files(mimeType, size)"
            ).execute()
            
            items = results.get('files', [])
            
            folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
            files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
            
            total_size = sum(int(f.get('size', 0)) for f in files if f.get('size'))
            
            print(f"✅ {len(folders)} pastas, {len(files)} arquivos, {total_size} bytes")
            
            return {
                'total_folders': len(folders),
                'total_files': len(files),
                'total_size': total_size,
                'total_items': len(items)
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular estatísticas: {e}")
            return {'total_folders': 0, 'total_files': 0, 'total_size': 0, 'total_items': 0}
    
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
    
    def rename_file(self, file_id: str, new_name: str) -> bool:
        """Renomeia um arquivo do Google Drive"""
        try:
            self.service.files().update(
                fileId=file_id,
                body={'name': new_name}
            ).execute()
            print(f"Arquivo renomeado para '{new_name}' com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao renomear arquivo: {e}")
            return False
    
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
    
    def create_employee_folder_structure(self, employee_folder_id: str, drive_id: str = None) -> Dict[str, Any]:
        """Cria a estrutura padrão de 12 pastas para um funcionário"""
        
        # Estrutura padrão de pastas
        folder_structure = [
            "01 - Documentos Pessoais",
            "02 - Documentos Admissionais e Periódicos",
            "03 - Sinistros",
            "04 - Férias",
            "05 - Dependentes",
            "06 - Certificados",
            "07 - IRPF",
            "08 - Multas de Trânsito",
            "09 - Plano de Saúde",
            "10 - Documentos Escaneados",
            "11 - Acordos",
            "12 - Rescisão"
        ]
        
        created_folders = []
        errors = []
        
        try:
            print(f"🔨 Criando estrutura de pastas para funcionário...")
            
            for folder_name in folder_structure:
                try:
                    folder_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [employee_folder_id]
                    }
                    
                    # Se for drive compartilhado, adiciona suporte
                    if drive_id:
                        folder = self.service.files().create(
                            body=folder_metadata,
                            fields='id, name',
                            supportsAllDrives=True
                        ).execute()
                    else:
                        folder = self.service.files().create(
                            body=folder_metadata,
                            fields='id, name'
                        ).execute()
                    
                    created_folders.append({
                        'id': folder['id'],
                        'name': folder['name']
                    })
                    print(f"   ✅ Criada: {folder_name}")
                    
                except Exception as e:
                    error_msg = f"Erro ao criar '{folder_name}': {str(e)}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            return {
                'success': len(errors) == 0,
                'created': created_folders,
                'errors': errors,
                'total_created': len(created_folders),
                'total_errors': len(errors)
            }
            
        except Exception as e:
            return {
                'success': False,
                'created': created_folders,
                'errors': [str(e)],
                'total_created': len(created_folders),
                'total_errors': 1
            }
    
    def validate_employee_structure(self, employee_folder_id: str, drive_id: str = None) -> Dict[str, Any]:
        """Valida e retorna quais pastas estão faltando na estrutura do funcionário"""
        
        # Estrutura padrão esperada
        expected_folders = [
            "01 - Documentos Pessoais",
            "02 - Documentos Admissionais e Periódicos",
            "03 - Sinistros",
            "04 - Férias",
            "05 - Dependentes",
            "06 - Certificados",
            "07 - IRPF",
            "08 - Multas de Trânsito",
            "09 - Plano de Saúde",
            "10 - Documentos Escaneados",
            "11 - Acordos",
            "12 - Rescisão"
        ]
        
        try:
            # Lista pastas existentes
            if drive_id:
                query = f"'{employee_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results = self.service.files().list(
                    q=query,
                    driveId=drive_id,
                    corpora='drive',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields='files(id, name)',
                    pageSize=100
                ).execute()
            else:
                query = f"'{employee_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results = self.service.files().list(
                    q=query,
                    fields='files(id, name)',
                    pageSize=100
                ).execute()
            
            existing_folders = results.get('files', [])
            existing_names = [f['name'] for f in existing_folders]
            
            # Verifica quais pastas estão faltando
            missing_folders = [f for f in expected_folders if f not in existing_names]
            extra_folders = [f for f in existing_names if f not in expected_folders]
            
            # Calcula conformidade
            conformity_percentage = ((len(expected_folders) - len(missing_folders)) / len(expected_folders)) * 100
            
            return {
                'is_complete': len(missing_folders) == 0,
                'conformity_percentage': round(conformity_percentage, 1),
                'total_expected': len(expected_folders),
                'total_existing': len(existing_folders),
                'missing_folders': missing_folders,
                'extra_folders': extra_folders,
                'existing_folders': existing_names
            }
            
        except Exception as e:
            return {
                'is_complete': False,
                'conformity_percentage': 0,
                'error': str(e)
            }
    
    def complete_employee_structure(self, employee_folder_id: str, drive_id: str = None) -> Dict[str, Any]:
        """Valida e completa a estrutura de pastas de um funcionário"""
        
        # Primeiro valida
        validation = self.validate_employee_structure(employee_folder_id, drive_id)
        
        if validation.get('is_complete'):
            return {
                'success': True,
                'message': 'Estrutura já está completa',
                'validation': validation,
                'created': []
            }
        
        # Se há pastas faltando, cria elas
        missing_folders = validation.get('missing_folders', [])
        created_folders = []
        errors = []
        
        try:
            print(f"🔨 Completando estrutura... {len(missing_folders)} pastas faltando")
            
            for folder_name in missing_folders:
                try:
                    folder_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [employee_folder_id]
                    }
                    
                    if drive_id:
                        folder = self.service.files().create(
                            body=folder_metadata,
                            fields='id, name',
                            supportsAllDrives=True
                        ).execute()
                    else:
                        folder = self.service.files().create(
                            body=folder_metadata,
                            fields='id, name'
                        ).execute()
                    
                    created_folders.append({
                        'id': folder['id'],
                        'name': folder['name']
                    })
                    print(f"   ✅ Criada: {folder_name}")
                    
                except Exception as e:
                    error_msg = f"Erro ao criar '{folder_name}': {str(e)}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            # Valida novamente após criar
            new_validation = self.validate_employee_structure(employee_folder_id, drive_id)
            
            return {
                'success': len(errors) == 0,
                'message': f'Estrutura completada. {len(created_folders)} pastas criadas.',
                'validation_before': validation,
                'validation_after': new_validation,
                'created': created_folders,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao completar estrutura: {str(e)}',
                'created': created_folders,
                'errors': errors
            }
