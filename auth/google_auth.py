import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GOOGLE_APPLICATION_CREDENTIALS, SCOPES, TOKEN_FILE


class GoogleAuth:
    """Classe para gerenciar autenticação com APIs do Google"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        
    def authenticate(self):
        """Autentica com as APIs do Google usando OAuth 2.0"""
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
                creds = flow.run_local_server(port=0)
            
            # Salva as credenciais para próximas execuções
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return creds
    
    def get_sheets_service(self):
        """Retorna o serviço do Google Sheets"""
        if not self.credentials:
            self.authenticate()
        
        if not self.service:
            self.service = build('sheets', 'v4', credentials=self.credentials)
        
        return self.service
    
    def get_drive_service(self):
        """Retorna o serviço do Google Drive"""
        if not self.credentials:
            self.authenticate()
        
        return build('drive', 'v3', credentials=self.credentials)
    
    def get_gmail_service(self):
        """Retorna o serviço do Gmail"""
        if not self.credentials:
            self.authenticate()
        
        return build('gmail', 'v1', credentials=self.credentials)
    
    def revoke_credentials(self):
        """Revoga as credenciais salvas"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        print("Credenciais revogadas com sucesso!")


# Instância global para facilitar o uso
google_auth = GoogleAuth()
