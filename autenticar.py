#!/usr/bin/env python3
"""
Script para autenticação inicial com todas as APIs do Google
"""

from auth.google_auth import google_auth

print("=" * 60)
print("Autenticação com Google APIs")
print("=" * 60)
print()
print("Este script irá abrir seu navegador para autorizar o acesso às APIs:")
print("- Gmail API")
print("- Google Sheets API")
print("- Google Drive API")
print()
print("Por favor, faça login com sua conta Google e autorize as permissões.")
print()

try:
    # Autentica e obtém os serviços
    print("Iniciando autenticação...")
    creds = google_auth.authenticate()
    
    print("\n✅ Autenticação realizada com sucesso!")
    print()
    print("Testando acesso às APIs...")
    
    # Testa Gmail
    try:
        gmail_service = google_auth.get_gmail_service()
        profile = gmail_service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail: {profile.get('emailAddress')}")
    except Exception as e:
        print(f"❌ Gmail: {e}")
    
    # Testa Drive
    try:
        drive_service = google_auth.get_drive_service()
        about = drive_service.about().get(fields="user").execute()
        print(f"✅ Drive: {about['user'].get('emailAddress')}")
    except Exception as e:
        print(f"❌ Drive: {e}")
    
    # Testa Sheets
    try:
        sheets_service = google_auth.get_sheets_service()
        print(f"✅ Sheets: Serviço configurado")
    except Exception as e:
        print(f"❌ Sheets: {e}")
    
    print()
    print("=" * 60)
    print("Autenticação concluída! Você já pode usar a aplicação.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Erro durante autenticação: {e}")
    print()
    print("Verifique se:")
    print("1. O arquivo credentials.json está presente")
    print("2. As APIs estão ativadas no Google Cloud Console")
    print("3. Você tem permissão para acessar as APIs")
