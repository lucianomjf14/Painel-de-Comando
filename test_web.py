#!/usr/bin/env python3
"""
Teste simples da aplicação web
"""

from app import app

if __name__ == '__main__':
    print("Testando aplicacao web...")
    print("Acesse: http://localhost:5000")
    print("Pressione Ctrl+C para parar")
    
    try:
        app.run(debug=False, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\nAplicacao encerrada pelo usuario")
    except Exception as e:
        print(f"Erro: {e}")
