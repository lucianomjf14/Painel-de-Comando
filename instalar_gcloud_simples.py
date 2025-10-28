#!/usr/bin/env python3
"""
Script simplificado para instalação do Google Cloud CLI
"""

import subprocess
import os
import sys


def verificar_gcloud():
    """Verifica se o Google Cloud CLI está instalado"""
    try:
        resultado = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return resultado.returncode == 0
    except:
        return False


def instalar_via_winget():
    """Instala via winget"""
    print("Instalando Google Cloud CLI via winget...")
    try:
        resultado = subprocess.run(
            ["winget", "install", "Google.CloudSDK"],
            capture_output=True,
            text=True,
            timeout=300
        )
        return resultado.returncode == 0
    except:
        return False


def instalar_via_chocolatey():
    """Instala via Chocolatey"""
    print("Instalando Google Cloud CLI via Chocolatey...")
    try:
        resultado = subprocess.run(
            ["choco", "install", "gcloudsdk", "-y"],
            capture_output=True,
            text=True,
            timeout=300
        )
        return resultado.returncode == 0
    except:
        return False


def configurar_projeto():
    """Configura o projeto após instalação"""
    print("\n=== Configurando Google Cloud ===")
    
    # Login
    print("1. Fazendo login...")
    subprocess.run(["gcloud", "auth", "login"])
    
    # Criar projeto
    project_id = input("\nDigite o ID do projeto (ou pressione Enter para 'google-sheets-automation'): ").strip()
    if not project_id:
        project_id = "google-sheets-automation"
    
    print(f"2. Criando projeto: {project_id}")
    subprocess.run(["gcloud", "projects", "create", project_id])
    
    # Definir projeto ativo
    print(f"3. Definindo projeto ativo: {project_id}")
    subprocess.run(["gcloud", "config", "set", "project", project_id])
    
    # Ativar APIs
    print("4. Ativando APIs...")
    subprocess.run(["gcloud", "services", "enable", "sheets.googleapis.com"])
    subprocess.run(["gcloud", "services", "enable", "drive.googleapis.com"])
    
    # Criar credenciais
    print("5. Criando credenciais...")
    subprocess.run(["gcloud", "auth", "application-default", "login"])
    
    print("\nConfiguracao concluida!")


def main():
    print("Instalador Google Cloud CLI")
    print("=" * 40)
    
    # Verificar se já está instalado
    if verificar_gcloud():
        print("Google Cloud CLI ja esta instalado!")
        configurar_projeto()
        return
    
    print("Google Cloud CLI nao encontrado. Instalando...")
    
    # Tentar instalar
    if instalar_via_winget():
        print("Instalado via winget!")
    elif instalar_via_chocolatey():
        print("Instalado via Chocolatey!")
    else:
        print("Falha na instalacao automatica.")
        print("\nInstalacao manual:")
        print("1. Acesse: https://cloud.google.com/sdk/docs/install")
        print("2. Baixe o instalador para Windows")
        print("3. Execute o instalador")
        print("4. Reinicie o terminal")
        print("5. Execute: python configurar_google_cloud.py")
        return
    
    # Verificar instalação
    if verificar_gcloud():
        configurar_projeto()
    else:
        print("Instalacao concluida, mas gcloud nao foi encontrado.")
        print("Reinicie o terminal e execute novamente este script.")


if __name__ == "__main__":
    main()
