#!/usr/bin/env python3
"""
Teste das APIs do Google
"""

def test_gmail():
    """Testa API do Gmail"""
    try:
        from gmail.gmail_manager import GmailManager
        gmail = GmailManager()
        count = gmail.get_unread_count()
        print(f"OK Gmail API: {count} mensagens nao lidas")
        return True
    except Exception as e:
        print(f"ERRO Gmail API: {e}")
        return False

def test_sheets():
    """Testa API do Sheets"""
    try:
        from sheets.sheets_manager import GoogleSheetsManager
        sheets = GoogleSheetsManager()
        print("OK Sheets API: Inicializada com sucesso")
        return True
    except Exception as e:
        print(f"ERRO Sheets API: {e}")
        return False

def test_drive():
    """Testa API do Drive"""
    try:
        from drive.drive_manager import GoogleDriveManager
        drive = GoogleDriveManager()
        print("OK Drive API: Inicializada com sucesso")
        return True
    except Exception as e:
        print(f"ERRO Drive API: {e}")
        return False

def main():
    print("Testando APIs do Google...")
    print("=" * 40)
    
    gmail_ok = test_gmail()
    sheets_ok = test_sheets()
    drive_ok = test_drive()
    
    print("=" * 40)
    if gmail_ok and sheets_ok and drive_ok:
        print("SUCESSO: Todas as APIs estao funcionando!")
    else:
        print("ATENCAO: Algumas APIs apresentaram problemas")
    
    return gmail_ok and sheets_ok and drive_ok

if __name__ == "__main__":
    main()
