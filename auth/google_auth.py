import os
import pickle
import ssl
import time
import socket
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_APPLICATION_CREDENTIALS, SCOPES, TOKEN_FILE
import sys


def _retry_on_error(func, max_retries=3, retry_delay=2):
    """Executa função com retry em caso de erro SSL, Timeout ou HTTP 5xx"""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = func()
            return result
        except (ssl.SSLError, socket.timeout, TimeoutError, ConnectionError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                error_type = type(e).__name__
                print(f"Erro {error_type} na autenticação (tentativa {attempt + 1}/{max_retries}). Aguardando {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"⚠️  Erro de rede persistente na autenticação: {error_type}")
                return None
        except HttpError as e:
            # Retry para erros HTTP 5xx
            if e.resp.status >= 500 and attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Erro HTTP {e.resp.status} na autenticação (tentativa {attempt + 1}/{max_retries}). Aguardando {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"⚠️  Erro HTTP na autenticação: {e.resp.status}")
                return None
        except Exception as e:
            print(f"⚠️  Erro inesperado na autenticação: {type(e).__name__}: {str(e)[:100]}")
            return None
    return None


class GoogleAuth:
    """Classe para gerenciar autenticação com APIs do Google"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        # Carrega credenciais automaticamente se existirem
        self._load_existing_credentials()
    
    def _load_existing_credentials(self):
        """Carrega credenciais salvas se existirem"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                
                # Verifica se as credenciais são válidas
                if creds and creds.valid:
                    self.credentials = creds
                elif creds and creds.expired and creds.refresh_token:
                    # Tenta renovar credenciais expiradas
                    creds.refresh(Request())
                    self.credentials = creds
                    # Salva credenciais renovadas
                    with open(TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
        except Exception as e:
            print(f"Erro ao carregar credenciais: {e}")
            self.credentials = None
        
    def authenticate(self):
        """Autentica com as APIs do Google usando OAuth 2.0"""
        # Se já temos credenciais válidas, retorna
        if self.credentials and self.credentials.valid:
            return self.credentials
        
        creds = None
        
        # Verifica se já existe um token salvo
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # Se não há credenciais válidas, solicita autorização
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
                    raise FileNotFoundError(
                        f"Arquivo de credenciais não encontrado: {GOOGLE_APPLICATION_CREDENTIALS}\n"
                        "Por favor, baixe o arquivo credentials.json do Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_APPLICATION_CREDENTIALS, SCOPES)
                
                # Detecta se está em ambiente remoto (Codespaces, SSH, etc)
                is_remote = os.environ.get('CODESPACES') or os.environ.get('SSH_CONNECTION')
                
                if is_remote:
                    # Método manual para ambientes remotos
                    print("\n" + "="*60)
                    print("AUTENTICAÇÃO MANUAL (Ambiente Remoto Detectado)")
                    print("="*60)
                    
                    # Configura redirect_uri para urn:ietf:wg:oauth:2.0:oob (Out of Band)
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    # Gera URL de autorização
                    auth_url, _ = flow.authorization_url(
                        prompt='consent',
                        access_type='offline',
                        include_granted_scopes='true'
                    )
                    
                    print("\n1. Acesse esta URL no seu navegador:")
                    print(f"\n{auth_url}\n")
                    print("2. Após autorizar, o Google mostrará um CÓDIGO.")
                    print("3. Copie esse código e cole abaixo.")
                    print("\n" + "="*60)
                    
                    # Solicita o código manualmente
                    code = input("\nCole o código de autorização aqui: ").strip()
                    
                    # Remove possíveis caracteres extras
                    if 'code=' in code:
                        code = code.split('code=')[1].split('&')[0]
                    
                    # Troca o código por credenciais
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                else:
                    # Método padrão para ambientes locais - tenta múltiplas portas
                    ports_to_try = [0, 8080, 8081, 8082, 8083, 8084, 8085]
                    
                    for port in ports_to_try:
                        try:
                            print(f"Tentando porta {port if port != 0 else 'aleatória'}...")
                            creds = flow.run_local_server(port=port)
                            print(f"✅ Autenticação bem-sucedida na porta {port}!")
                            break
                        except Exception as e:
                            if port == ports_to_try[-1]:
                                # Se todas as portas falharam, usa método manual
                                print(f"\n⚠️  Erro ao usar servidor local: {e}")
                                print("\n Usando método manual...")
                                
                                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                                auth_url, _ = flow.authorization_url(
                                    prompt='consent',
                                    access_type='offline',
                                    include_granted_scopes='true'
                                )
                                
                                print("\n" + "="*60)
                                print("1. Acesse esta URL no seu navegador:")
                                print(f"\n{auth_url}\n")
                                print("2. Copie o código de autorização")
                                print("="*60)
                                
                                code = input("\nCole o código aqui: ").strip()
                                if 'code=' in code:
                                    code = code.split('code=')[1].split('&')[0]
                                
                                flow.fetch_token(code=code)
                                creds = flow.credentials
                            else:
                                continue
            
            # Salva as credenciais para próximas execuções
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return creds
    
    def get_sheets_service(self):
        """Retorna o serviço do Google Sheets"""
        if not self.credentials:
            self.authenticate()
        
        if not self.service or not hasattr(self, '_sheets_service'):
            # cache_discovery=False para evitar problemas de memória
            # timeout configurado via parâmetro do build
            self._sheets_service = build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)
            self.service = self._sheets_service
        
        return self._sheets_service
    
    def get_drive_service(self):
        """Retorna o serviço do Google Drive"""
        if not self.credentials:
            self.authenticate()
        
        if not hasattr(self, '_drive_service'):
            # cache_discovery=False para evitar problemas de memória
            self._drive_service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        
        return self._drive_service
    
    def get_gmail_service(self):
        """Retorna o serviço do Gmail"""
        if not self.credentials:
            self.authenticate()
        
        if not hasattr(self, '_gmail_service'):
            # cache_discovery=False para evitar problemas de memória
            self._gmail_service = build('gmail', 'v1', credentials=self.credentials, cache_discovery=False)
        
        return self._gmail_service
    
    def revoke_credentials(self):
        """Revoga as credenciais salvas"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        print("Credenciais revogadas com sucesso!")

    def is_authenticated(self) -> bool:
        """Verifica se as credenciais são válidas."""
        return self.credentials and self.credentials.valid
    
    def get_oauth_user_info(self) -> Optional[Dict[str, Any]]:
        """Busca informações do usuário (nome, email, foto) com retries."""
        if not self.credentials or not self.credentials.valid:
            print("⚠️  Erro: Não autenticado ao buscar user info.")
            return None
            
        def _fetch_user_info():
            oauth2_service = build('oauth2', 'v2', credentials=self.credentials, cache_discovery=False)
            return oauth2_service.userinfo().get().execute()

        # Usa a função de retry
        return _retry_on_error(_fetch_user_info)


# Instância global para facilitar o uso
google_auth = GoogleAuth()
