#!/usr/bin/env python3
"""
Teste da API de status da aplicação web
"""

import requests
import json

def test_status_api():
    """Testa a API de status"""
    try:
        response = requests.get('http://localhost:5000/api/status')
        if response.status_code == 200:
            data = response.json()
            print("API Status Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            print("\nResumo:")
            print(f"Status: {data.get('status')}")
            print(f"Autenticado: {data.get('authenticated')}")
            print(f"Mensagem: {data.get('message')}")
            
            if 'apis' in data:
                print("\nAPIs individuais:")
                for api, status in data['apis'].items():
                    status_text = "OK" if status else "ERRO"
                    print(f"  {api}: {status_text}")
            
            return True
        else:
            print(f"Erro HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"Erro ao testar API: {e}")
        return False

if __name__ == "__main__":
    print("Testando API de status...")
    print("=" * 40)
    test_status_api()
