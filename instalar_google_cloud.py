#!/usr/bin/env python3
"""
Script para instalação e configuração completa do Google Cloud CLI
"""

import subprocess
import os
import sys
import urllib.request
import zipfile
import tempfile
import shutil


def baixar_e_instalar_gcloud():
    """Baixa e instala o Google Cloud CLI"""
    print("=== Instalando Google Cloud CLI ===")
    
    try:
        # URL do instalador do Google Cloud CLI para Windows
        url = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
        
        print("Baixando Google Cloud CLI...")
        with urllib.request.urlopen(url) as response:
            with open("GoogleCloudSDKInstaller.exe", "wb") as f:
                f.write(response.read())
        
        print("✅ Download concluído!")
        print("📋 Para instalar:")
        print("1. Execute: GoogleCloudSDKInstaller.exe")
        print("2. Siga as instruções do instalador")
        print("3. Reinicie o terminal após a instalação")
        print("4. Execute novamente este script")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        return False


def instalar_via_winget():
    """Tenta instalar via winget (Windows Package Manager)"""
    print("=== Tentando instalar via winget ===")
    
    try:
        resultado = subprocess.run(
            ["winget", "install", "Google.CloudSDK"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if resultado.returncode == 0:
            print("✅ Google Cloud CLI instalado via winget!")
            return True
        else:
            print(f"❌ Falha no winget: {resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no winget: {e}")
        return False


def instalar_via_chocolatey():
    """Tenta instalar via Chocolatey"""
    print("=== Tentando instalar via Chocolatey ===")
    
    try:
        resultado = subprocess.run(
            ["choco", "install", "gcloudsdk", "-y"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if resultado.returncode == 0:
            print("✅ Google Cloud CLI instalado via Chocolatey!")
            return True
        else:
            print(f"❌ Falha no Chocolatey: {resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no Chocolatey: {e}")
        return False


def verificar_instalacao():
    """Verifica se o Google Cloud CLI foi instalado"""
    print("=== Verificando Instalação ===")
    
    try:
        resultado = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if resultado.returncode == 0:
            print(f"✅ Google Cloud CLI encontrado: {resultado.stdout.split()[0]}")
            return True
        else:
            print("❌ Google Cloud CLI não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")
        return False


def configurar_apos_instalacao():
    """Configura o Google Cloud após a instalação"""
    print("\n=== Configuração Pós-Instalação ===")
    
    # 1. Login
    print("1. Fazendo login...")
    resultado = subprocess.run(["gcloud", "auth", "login"], timeout=300)
    if resultado.returncode != 0:
        print("❌ Falha no login")
        return False
    
    # 2. Criar projeto
    project_id = input("\nDigite o ID do projeto (ou pressione Enter para 'google-sheets-automation'): ").strip()
    if not project_id:
        project_id = "google-sheets-automation"
    
    print(f"2. Criando projeto: {project_id}")
    resultado = subprocess.run(["gcloud", "projects", "create", project_id], capture_output=True, text=True)
    if resultado.returncode != 0 and "already exists" not in resultado.stderr:
        print(f"❌ Falha ao criar projeto: {resultado.stderr}")
        return False
    
    # 3. Definir projeto ativo
    print(f"3. Definindo projeto ativo: {project_id}")
    resultado = subprocess.run(["gcloud", "config", "set", "project", project_id])
    if resultado.returncode != 0:
        print("❌ Falha ao definir projeto")
        return False
    
    # 4. Ativar APIs
    print("4. Ativando APIs...")
    apis = ["sheets.googleapis.com", "drive.googleapis.com"]
    for api in apis:
        resultado = subprocess.run(["gcloud", "services", "enable", api])
        if resultado.returncode != 0:
            print(f"❌ Falha ao ativar {api}")
            return False
    
    # 5. Criar credenciais
    print("5. Criando credenciais...")
    resultado = subprocess.run(["gcloud", "auth", "application-default", "login"])
    if resultado.returncode != 0:
        print("❌ Falha ao criar credenciais")
        return False
    
    print("\n🎉 Configuração concluída!")
    return True


def main():
    """Função principal"""
    print("Instalador Automático - Google Cloud CLI")
    print("=" * 50)
    
    # Verificar se já está instalado
    if verificar_instalacao():
        print("✅ Google Cloud CLI já está instalado!")
        configurar_apos_instalacao()
        return
    
    print("Google Cloud CLI não encontrado. Tentando instalar...\n")
    
    # Tentar diferentes métodos de instalação
    metodos = [
        ("winget", instalar_via_winget),
        ("chocolatey", instalar_via_chocolatey),
        ("download manual", baixar_e_instalar_gcloud)
    ]
    
    for nome, metodo in metodos:
        print(f"\n--- Tentando instalar via {nome} ---")
        if metodo():
            if verificar_instalacao():
                configurar_apos_instalacao()
                return
            else:
                print(f"⚠️  Instalação via {nome} concluída, mas gcloud não foi encontrado")
                print("   Reinicie o terminal e execute novamente este script")
                return
    
    print("\n❌ Não foi possível instalar o Google Cloud CLI automaticamente")
    print("\n📋 Instalação Manual:")
    print("1. Acesse: https://cloud.google.com/sdk/docs/install")
    print("2. Baixe o instalador para Windows")
    print("3. Execute o instalador")
    print("4. Reinicie o terminal")
    print("5. Execute: python configurar_google_cloud.py")


if __name__ == "__main__":
    main()
