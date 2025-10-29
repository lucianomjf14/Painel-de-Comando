#!/usr/bin/env python3
"""Script para verificar se o token está válido"""

import pickle
import os
from google.auth.transport.requests import Request

TOKEN_FILE = 'token.pickle'

try:
    if os.path.exists(TOKEN_FILE):
        print(f"Arquivo {TOKEN_FILE} encontrado")
        
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)
        
        print(f"Token carregado com sucesso")
        print(f"Token válido: {credentials.valid}")
        print(f"Token expirado: {credentials.expired}")
        print(f"Token possui refresh token: {credentials.refresh_token is not None}")
        
        if credentials.expired and credentials.refresh_token:
            print("\nToken expirado. Tentando renovar...")
            credentials.refresh(Request())
            print("Token renovado com sucesso!")
            
            # Salva o token renovado
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(credentials, token)
            print(f"Token salvo em {TOKEN_FILE}")
        
        print(f"\nToken válido após verificação: {credentials.valid}")
        print(f"Scopes: {credentials.scopes}")
        
    else:
        print(f"Arquivo {TOKEN_FILE} não encontrado!")
        print("Execute: python autenticar.py")
        
except Exception as e:
    print(f"Erro ao verificar token: {e}")
    import traceback
    traceback.print_exc()
