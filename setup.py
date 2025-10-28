#!/usr/bin/env python3
"""
Script de instalação e configuração para automação Google Sheets/Drive
"""

import os
import sys
import subprocess
import json


def instalar_dependencias():
    """Instala as dependências necessárias"""
    print("Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def verificar_credenciais():
    """Verifica se as credenciais estão configuradas"""
    if os.path.exists("credentials.json"):
        print("✅ Arquivo credentials.json encontrado!")
        return True
    else:
        print("❌ Arquivo credentials.json não encontrado!")
        print("\nPara configurar as credenciais:")
        print("1. Acesse https://console.cloud.google.com/")
        print("2. Crie um novo projeto ou selecione um existente")
        print("3. Ative as APIs: Google Sheets API e Google Drive API")
        print("4. Crie credenciais OAuth 2.0 (Aplicação Desktop)")
        print("5. Baixe o arquivo JSON e renomeie para 'credentials.json'")
        print("6. Coloque o arquivo na raiz deste projeto")
        return False


def criar_arquivo_env():
    """Cria arquivo .env se não existir"""
    if not os.path.exists(".env"):
        env_content = """GOOGLE_APPLICATION_CREDENTIALS=credentials.json
SCOPES=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive
TOKEN_FILE=token.json"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Arquivo .env criado!")
    else:
        print("✅ Arquivo .env já existe!")


def testar_conexao():
    """Testa a conexão com as APIs do Google"""
    try:
        from auth.google_auth import google_auth
        print("Testando conexão com Google APIs...")
        google_auth.authenticate()
        print("✅ Conexão estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False


def main():
    """Função principal de instalação"""
    print("=== Instalação e Configuração - Google Sheets/Drive Automation ===\n")
    
    # 1. Instalar dependências
    if not instalar_dependencias():
        return False
    
    print("\n" + "="*50 + "\n")
    
    # 2. Verificar credenciais
    if not verificar_credenciais():
        print("\n⚠️  Configure as credenciais antes de continuar!")
        return False
    
    print("\n" + "="*50 + "\n")
    
    # 3. Criar arquivo .env
    criar_arquivo_env()
    
    print("\n" + "="*50 + "\n")
    
    # 4. Testar conexão
    if testar_conexao():
        print("\n🎉 Instalação concluída com sucesso!")
        print("\nPróximos passos:")
        print("1. Execute: python cli.py auth login")
        print("2. Teste com: python exemplo.py")
        print("3. Use os comandos: python cli.py --help")
        return True
    else:
        print("\n❌ Instalação falhou na etapa de teste de conexão")
        return False


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
