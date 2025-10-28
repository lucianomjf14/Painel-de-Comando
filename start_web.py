#!/usr/bin/env python3
"""
Script para iniciar a aplicação web do Google Automation Dashboard
"""

import os
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Abre o navegador após 2 segundos"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    print("Iniciando Google Automation Dashboard...")
    print("=" * 50)
    print("Gmail: http://localhost:5000/gmail")
    print("Sheets: http://localhost:5000/sheets")
    print("Drive: http://localhost:5000/drive")
    print("Home: http://localhost:5000")
    print("=" * 50)
    print("Aguarde alguns segundos para o servidor inicializar...")
    print("O navegador sera aberto automaticamente")
    print("=" * 50)
    
    # Abre o navegador após 2 segundos
    Timer(2.0, open_browser).start()
    
    # Importa e executa a aplicação Flask
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"Erro ao importar a aplicacao: {e}")
        print("Certifique-se de que todas as dependencias estao instaladas:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao iniciar a aplicacao: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
