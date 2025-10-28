#!/usr/bin/env python3
"""
Script para configuração automática do Google Cloud via CLI
"""

import subprocess
import json
import os
import sys
import time


def executar_comando(comando, descricao=""):
    """Executa um comando e retorna o resultado"""
    print(f"Executando: {descricao}")
    print(f"Comando: {comando}")
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding='utf-8')
        if resultado.returncode == 0:
            print(f"✅ Sucesso: {descricao}")
            return True, resultado.stdout
        else:
            print(f"❌ Erro: {descricao}")
            print(f"Erro: {resultado.stderr}")
            return False, resultado.stderr
    except Exception as e:
        print(f"❌ Exceção: {descricao} - {e}")
        return False, str(e)


def verificar_gcloud():
    """Verifica se o Google Cloud CLI está instalado"""
    print("=== Verificando Google Cloud CLI ===")
    
    sucesso, output = executar_comando("gcloud --version", "Verificar versão do gcloud")
    
    if not sucesso:
        print("\n❌ Google Cloud CLI não está instalado!")
        print("\nPara instalar:")
        print("1. Acesse: https://cloud.google.com/sdk/docs/install")
        print("2. Baixe e instale o Google Cloud CLI")
        print("3. Reinicie o terminal")
        return False
    
    print(f"✅ Google Cloud CLI encontrado: {output.split()[0]}")
    return True


def fazer_login():
    """Faz login no Google Cloud"""
    print("\n=== Fazendo Login no Google Cloud ===")
    
    sucesso, output = executar_comando("gcloud auth login", "Login no Google Cloud")
    
    if sucesso:
        print("✅ Login realizado com sucesso!")
        return True
    else:
        print("❌ Falha no login")
        return False


def criar_projeto(project_id):
    """Cria um novo projeto no Google Cloud"""
    print(f"\n=== Criando Projeto: {project_id} ===")
    
    # Verifica se o projeto já existe
    sucesso, output = executar_comando(f"gcloud projects describe {project_id}", "Verificar se projeto existe")
    
    if sucesso:
        print(f"✅ Projeto {project_id} já existe!")
        return True
    
    # Cria o projeto
    sucesso, output = executar_comando(f"gcloud projects create {project_id}", f"Criar projeto {project_id}")
    
    if sucesso:
        print(f"✅ Projeto {project_id} criado com sucesso!")
        return True
    else:
        print(f"❌ Falha ao criar projeto: {output}")
        return False


def definir_projeto(project_id):
    """Define o projeto ativo"""
    print(f"\n=== Definindo Projeto Ativo: {project_id} ===")
    
    sucesso, output = executar_comando(f"gcloud config set project {project_id}", f"Definir projeto ativo")
    
    if sucesso:
        print(f"✅ Projeto {project_id} definido como ativo!")
        return True
    else:
        print(f"❌ Falha ao definir projeto: {output}")
        return False


def ativar_apis():
    """Ativa as APIs necessárias"""
    print("\n=== Ativando APIs Necessárias ===")
    
    apis = [
        "sheets.googleapis.com",
        "drive.googleapis.com"
    ]
    
    for api in apis:
        print(f"Ativando {api}...")
        sucesso, output = executar_comando(f"gcloud services enable {api}", f"Ativar {api}")
        
        if sucesso:
            print(f"✅ {api} ativada com sucesso!")
        else:
            print(f"❌ Falha ao ativar {api}: {output}")
            return False
    
    return True


def criar_credenciais_oauth():
    """Cria credenciais OAuth 2.0"""
    print("\n=== Criando Credenciais OAuth 2.0 ===")
    
    # Cria o cliente OAuth
    sucesso, output = executar_comando(
        'gcloud auth application-default login',
        "Criar credenciais de aplicação padrão"
    )
    
    if sucesso:
        print("✅ Credenciais de aplicação padrão criadas!")
        return True
    else:
        print("❌ Falha ao criar credenciais de aplicação padrão")
        print("Tentando método alternativo...")
        
        # Método alternativo: criar credenciais OAuth via console
        print("\n📋 Para criar credenciais OAuth 2.0 manualmente:")
        print("1. Acesse: https://console.cloud.google.com/apis/credentials")
        print("2. Clique em 'Criar Credenciais' > 'ID do cliente OAuth 2.0'")
        print("3. Tipo: Aplicação Desktop")
        print("4. Baixe o arquivo JSON")
        print("5. Renomeie para 'credentials.json' e coloque na raiz do projeto")
        
        return False


def criar_arquivo_credenciais_manual():
    """Cria um arquivo de credenciais manual para configuração"""
    print("\n=== Criando Arquivo de Configuração Manual ===")
    
    # Obtém informações do projeto atual
    sucesso, output = executar_comando("gcloud config get-value project", "Obter projeto atual")
    
    if not sucesso:
        print("❌ Não foi possível obter o projeto atual")
        return False
    
    project_id = output.strip()
    
    # Cria instruções detalhadas
    instrucoes = f"""
# Instruções para Configuração Manual das Credenciais

## Projeto Atual: {project_id}

### Passo 1: Acessar o Console do Google Cloud
1. Abra: https://console.cloud.google.com/apis/credentials?project={project_id}

### Passo 2: Criar Credenciais OAuth 2.0
1. Clique em "Criar Credenciais" > "ID do cliente OAuth 2.0"
2. Tipo de aplicação: "Aplicação Desktop"
3. Nome: "Google Sheets/Drive Automation"
4. Clique em "Criar"

### Passo 3: Baixar Credenciais
1. Clique no ícone de download (⬇️) ao lado das credenciais criadas
2. Salve o arquivo como "credentials.json" na raiz deste projeto

### Passo 4: Testar Configuração
Execute: python cli.py auth login
"""
    
    with open("CONFIGURACAO_CREDENCIAIS.md", "w", encoding="utf-8") as f:
        f.write(instrucoes)
    
    print("✅ Arquivo de instruções criado: CONFIGURACAO_CREDENCIAIS.md")
    return True


def configurar_automaticamente():
    """Configuração automática completa"""
    print("=== Configuração Automática do Google Cloud ===\n")
    
    # 1. Verificar gcloud
    if not verificar_gcloud():
        return False
    
    # 2. Fazer login
    if not fazer_login():
        return False
    
    # 3. Obter ou criar projeto
    project_id = input("\nDigite o ID do projeto (ou pressione Enter para 'google-sheets-automation'): ").strip()
    if not project_id:
        project_id = "google-sheets-automation"
    
    # 4. Criar projeto se necessário
    if not criar_projeto(project_id):
        return False
    
    # 5. Definir projeto ativo
    if not definir_projeto(project_id):
        return False
    
    # 6. Ativar APIs
    if not ativar_apis():
        return False
    
    # 7. Criar credenciais
    if not criar_credenciais_oauth():
        print("\n⚠️  Não foi possível criar credenciais automaticamente")
        criar_arquivo_credenciais_manual()
        return False
    
    print("\n🎉 Configuração concluída com sucesso!")
    print("\nPróximos passos:")
    print("1. Execute: python cli.py auth login")
    print("2. Teste com: python exemplo.py")
    
    return True


def main():
    """Função principal"""
    print("Google Cloud CLI - Configuração Automática")
    print("=" * 50)
    
    try:
        configurar_automaticamente()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuração cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    main()
