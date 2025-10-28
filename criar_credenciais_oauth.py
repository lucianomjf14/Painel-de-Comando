#!/usr/bin/env python3
"""
Script para criar credenciais OAuth 2.0 para a aplicação
"""

import subprocess
import json
import os


def criar_credenciais_oauth():
    """Cria credenciais OAuth 2.0 para a aplicação"""
    print("=== Criando Credenciais OAuth 2.0 ===")
    
    # Caminho para o gcloud
    gcloud_path = r"C:\Users\Mantovani\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    
    # Criar credenciais OAuth
    print("1. Criando credenciais OAuth...")
    try:
        # Listar credenciais existentes
        resultado = subprocess.run(
            [gcloud_path, "iam", "service-accounts", "list"],
            capture_output=True,
            text=True
        )
        
        if resultado.returncode == 0:
            print("Contas de serviço existentes:")
            print(resultado.stdout)
        
        # Criar conta de serviço
        print("\n2. Criando conta de serviço...")
        resultado = subprocess.run([
            gcloud_path, "iam", "service-accounts", "create",
            "sheets-drive-automation",
            "--display-name", "Google Sheets Drive Automation",
            "--description", "Conta de serviço para automação de Sheets e Drive"
        ], capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Conta de serviço criada!")
        else:
            print(f"⚠️  Conta de serviço pode já existir: {resultado.stderr}")
        
        # Criar chave JSON
        print("\n3. Criando chave JSON...")
        resultado = subprocess.run([
            gcloud_path, "iam", "service-accounts", "keys", "create",
            "credentials.json",
            "--iam-account", "sheets-drive-automation@automation-sheets-drive.iam.gserviceaccount.com"
        ], capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Chave JSON criada: credentials.json")
            return True
        else:
            print(f"❌ Erro ao criar chave: {resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def configurar_credenciais_manuais():
    """Configura credenciais OAuth 2.0 manualmente"""
    print("\n=== Configuração Manual de Credenciais OAuth 2.0 ===")
    
    instrucoes = """
Para criar credenciais OAuth 2.0 manualmente:

1. Acesse: https://console.cloud.google.com/apis/credentials?project=automation-sheets-drive

2. Clique em "Criar Credenciais" > "ID do cliente OAuth 2.0"

3. Configure:
   - Tipo de aplicação: Aplicação Desktop
   - Nome: Google Sheets Drive Automation

4. Baixe o arquivo JSON

5. Renomeie para 'credentials.json' e coloque na raiz do projeto

6. Execute: python cli.py auth login
"""
    
    print(instrucoes)
    
    # Criar arquivo de instruções
    with open("INSTRUCOES_CREDENCIAIS.txt", "w", encoding="utf-8") as f:
        f.write(instrucoes)
    
    print("✅ Instruções salvas em: INSTRUCOES_CREDENCIAIS.txt")


def main():
    print("Configurador de Credenciais OAuth 2.0")
    print("=" * 50)
    
    # Tentar criar credenciais automaticamente
    if not criar_credenciais_oauth():
        print("\n⚠️  Criação automática falhou. Usando método manual...")
        configurar_credenciais_manuais()
    else:
        print("\n🎉 Credenciais OAuth 2.0 criadas com sucesso!")
        print("\nPróximos passos:")
        print("1. Execute: python cli.py auth login")
        print("2. Teste com: python exemplo.py")


if __name__ == "__main__":
    main()
