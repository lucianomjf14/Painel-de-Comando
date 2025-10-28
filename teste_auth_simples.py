#!/usr/bin/env python3
"""
Teste simples de autenticacao Google
"""

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import os

# Escopos necessarios
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def testar_autenticacao():
    """Testa a autenticacao com Google APIs"""
    print("Testando autenticacao com Google APIs...")
    
    creds = None
    
    # Verificar se existe token salvo
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Se nao ha credenciais validas, solicitar autorizacao
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERRO: Arquivo credentials.json nao encontrado!")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salvar credenciais
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("Autenticacao realizada com sucesso!")
    
    # Testar Google Sheets
    try:
        service = build('sheets', 'v4', credentials=creds)
        print("Google Sheets API: OK")
    except Exception as e:
        print(f"Erro Google Sheets: {e}")
    
    # Testar Google Drive
    try:
        service = build('drive', 'v3', credentials=creds)
        print("Google Drive API: OK")
    except Exception as e:
        print(f"Erro Google Drive: {e}")
    
    return True

if __name__ == "__main__":
    testar_autenticacao()
