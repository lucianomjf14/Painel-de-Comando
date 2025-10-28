#!/usr/bin/env python3
"""
Script para resolver o bloqueio da aplicação Gmail
"""

import webbrowser
import time


def resolver_bloqueio_gmail():
    """Resolve o bloqueio da aplicação Gmail"""
    print("=== Resolvendo Bloqueio da Aplicação Gmail ===")
    
    print("\nO erro indica que a aplicação está bloqueada pelo Google.")
    print("Isso acontece porque a aplicação está em modo de teste.")
    print("Vamos configurar corretamente:")
    
    print("\n1. Acesse o Console do Google Cloud:")
    print("   https://console.cloud.google.com/apis/credentials/consent?project=automation-sheets-drive")
    
    print("\n2. Configure a Tela de Consentimento OAuth:")
    print("   - Tipo de usuário: Externo")
    print("   - Status de publicação: TESTE (não publique)")
    print("   - Usuários de teste: adicione lucianomjf14@gmail.com")
    print("   - Escopos necessários:")
    print("     * https://www.googleapis.com/auth/spreadsheets")
    print("     * https://www.googleapis.com/auth/drive")
    print("     * https://www.googleapis.com/auth/gmail.modify")
    print("     * https://www.googleapis.com/auth/gmail.compose")
    print("     * https://www.googleapis.com/auth/gmail.readonly")
    
    print("\n3. Configure as Credenciais OAuth 2.0:")
    print("   https://console.cloud.google.com/apis/credentials?project=automation-sheets-drive")
    print("   - Edite a credencial OAuth 2.0")
    print("   - Adicione URIs de redirecionamento:")
    print("     * http://localhost:8080")
    print("     * http://localhost:8081")
    print("     * http://localhost:8082")
    print("     * http://localhost:8083")
    print("     * http://localhost:8084")
    print("     * http://localhost:8085")
    
    print("\n4. IMPORTANTE - Adicione seu email como usuário de teste:")
    print("   - Na tela de consentimento OAuth")
    print("   - Seção 'Usuários de teste'")
    print("   - Adicione: lucianomjf14@gmail.com")
    print("   - Salve as configurações")
    
    print("\n5. Aguarde alguns minutos para as configurações serem aplicadas")
    
    # Abrir consoles automaticamente
    print("\nAbrindo consoles automaticamente...")
    
    urls = [
        "https://console.cloud.google.com/apis/credentials/consent?project=automation-sheets-drive",
        "https://console.cloud.google.com/apis/credentials?project=automation-sheets-drive"
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"{i}. Abrindo: {url}")
        webbrowser.open(url)
        time.sleep(2)


def configurar_escopos_gmail():
    """Configura os escopos necessários para Gmail"""
    print("\n=== Configuração dos Escopos Gmail ===")
    
    print("\nEscopos necessários para Gmail:")
    print("1. https://www.googleapis.com/auth/gmail.readonly")
    print("   - Ler mensagens e metadados")
    print("2. https://www.googleapis.com/auth/gmail.modify")
    print("   - Modificar mensagens (marcar como lida, adicionar labels)")
    print("3. https://www.googleapis.com/auth/gmail.compose")
    print("   - Enviar emails")
    
    print("\nComo adicionar os escopos:")
    print("1. Acesse a tela de consentimento OAuth")
    print("2. Clique em 'Adicionar ou remover escopos'")
    print("3. Adicione os escopos do Gmail listados acima")
    print("4. Clique em 'Atualizar' e depois 'Salvar e continuar'")


def testar_apos_configuracao():
    """Testa a aplicação após configuração"""
    print("\n=== Teste Após Configuração ===")
    
    print("\nApós configurar tudo:")
    print("1. Aguarde 5-10 minutos")
    print("2. Execute: python cli.py auth login")
    print("3. Teste: python cli.py gmail unread-count")
    print("4. Se funcionar, execute: python exemplo.py")
    
    print("\nComandos de teste do Gmail:")
    print("- python cli.py gmail unread-count")
    print("- python cli.py gmail list")
    print("- python cli.py gmail labels")


def main():
    print("Resolvedor de Bloqueio Gmail")
    print("=" * 40)
    
    resolver_bloqueio_gmail()
    configurar_escopos_gmail()
    testar_apos_configuracao()
    
    print("\n" + "="*50)
    print("RESUMO:")
    print("1. Configure a tela de consentimento OAuth como 'TESTE'")
    print("2. Adicione seu email como usuário de teste")
    print("3. Adicione os escopos do Gmail")
    print("4. Configure as URIs de redirecionamento")
    print("5. Aguarde alguns minutos")
    print("6. Teste novamente")


if __name__ == "__main__":
    main()
