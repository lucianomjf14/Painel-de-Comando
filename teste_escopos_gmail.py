#!/usr/bin/env python3
"""
Script para testar escopos do Gmail
"""

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import os

# Escopos necessários para Gmail
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

def testar_escopos_gmail():
    """Testa se os escopos do Gmail estão funcionando"""
    print("Testando escopos do Gmail...")
    
    creds = None
    
    # Verificar se existe token salvo
    if os.path.exists('token_gmail.pickle'):
        with open('token_gmail.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Se não há credenciais válidas, solicitar autorização
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERRO: Arquivo credentials.json não encontrado!")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salvar credenciais
        with open('token_gmail.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("Autenticação realizada com sucesso!")
    
    # Testar Gmail
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Testar contagem de não lidas
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=1
        ).execute()
        
        count = results.get('resultSizeEstimate', 0)
        print(f"✅ Gmail API funcionando! Mensagens não lidas: {count}")
        
        # Testar listagem de labels
        labels = service.users().labels().list(userId='me').execute()
        print(f"✅ Labels encontrados: {len(labels.get('labels', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no Gmail: {e}")
        return False

if __name__ == "__main__":
    testar_escopos_gmail()
