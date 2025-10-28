#!/usr/bin/env python3
"""
Script para verificar e corrigir configuração do Gmail
"""

import webbrowser
import time


def verificar_configuracao_gmail():
    """Verifica se a configuração do Gmail está correta"""
    print("=== Verificação da Configuração Gmail ===")
    
    print("\nO erro 403 indica que os escopos do Gmail não foram configurados corretamente.")
    print("Vamos verificar e corrigir:")
    
    print("\n1. VERIFIQUE se adicionou os escopos do Gmail:")
    print("   - Acesse: https://console.cloud.google.com/apis/credentials/consent?project=automation-sheets-drive")
    print("   - Clique em 'Adicionar ou remover escopos'")
    print("   - Procure e adicione estes escopos:")
    print("     * Gmail API - gmail.readonly")
    print("     * Gmail API - gmail.modify") 
    print("     * Gmail API - gmail.compose")
    print("   - Clique em 'Atualizar' e depois 'Salvar e continuar'")
    
    print("\n2. VERIFIQUE se adicionou seu email como usuário de teste:")
    print("   - Na mesma tela de consentimento OAuth")
    print("   - Seção 'Usuários de teste'")
    print("   - Deve ter: lucianomjf14@gmail.com")
    print("   - Se não tiver, adicione e salve")
    
    print("\n3. VERIFIQUE se o status é 'TESTE' e não 'EM PRODUÇÃO':")
    print("   - Status deve ser 'TESTE'")
    print("   - NÃO clique em 'Publicar aplicativo'")
    
    # Abrir console
    print("\nAbrindo console de consentimento OAuth...")
    webbrowser.open("https://console.cloud.google.com/apis/credentials/consent?project=automation-sheets-drive")


def criar_script_teste_escopos():
    """Cria script para testar escopos"""
    print("\n=== Criando Script de Teste de Escopos ===")
    
    script_teste = '''#!/usr/bin/env python3
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
'''
    
    with open("teste_escopos_gmail.py", "w", encoding="utf-8") as f:
        f.write(script_teste)
    
    print("Script de teste criado: teste_escopos_gmail.py")


def instrucoes_detalhadas():
    """Fornece instruções detalhadas"""
    print("\n=== Instruções Detalhadas ===")
    
    print("\nPASSO A PASSO:")
    print("1. Acesse o console de consentimento OAuth")
    print("2. Clique em 'Adicionar ou remover escopos'")
    print("3. Na busca, digite 'Gmail'")
    print("4. Adicione estes 3 escopos:")
    print("   - Gmail API - gmail.readonly")
    print("   - Gmail API - gmail.modify")
    print("   - Gmail API - gmail.compose")
    print("5. Clique em 'Atualizar'")
    print("6. Clique em 'Salvar e continuar'")
    print("7. Na seção 'Usuários de teste', adicione:")
    print("   - lucianomjf14@gmail.com")
    print("8. Clique em 'Salvar e continuar'")
    print("9. Aguarde 5-10 minutos")
    print("10. Execute: python teste_escopos_gmail.py")


def main():
    print("Verificador de Configuração Gmail")
    print("=" * 40)
    
    verificar_configuracao_gmail()
    criar_script_teste_escopos()
    instrucoes_detalhadas()
    
    print("\n" + "="*50)
    print("APÓS CONFIGURAR:")
    print("1. Aguarde 5-10 minutos")
    print("2. Execute: python teste_escopos_gmail.py")
    print("3. Se funcionar, execute: python cli.py gmail unread-count")


if __name__ == "__main__":
    main()
