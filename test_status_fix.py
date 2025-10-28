#!/usr/bin/env python3
"""
Teste da correção do status das APIs
"""

import requests
import time

def test_status_fix():
    """Testa se a correção do status funcionou"""
    try:
        # Aguarda a aplicação inicializar
        time.sleep(3)
        
        # Testa a API de status
        response = requests.get('http://localhost:5000/api/status')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API de status funcionando!")
            print(f"Status: {data.get('status')}")
            print(f"Autenticado: {data.get('authenticated')}")
            
            if 'apis' in data:
                print("\n📊 Status das APIs:")
                for api, status in data['apis'].items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {api}: {status_icon}")
                
                print("\n🌐 Acesse http://localhost:5000 no navegador")
                print("🔍 Abra o Console do navegador (F12) para ver os logs de debug")
                print("📱 O status deve mostrar 'Funcionando' em vez de 'Verificando...'")
                
                return True
            else:
                print("❌ Campo 'apis' não encontrado na resposta")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testando correção do status das APIs...")
    print("=" * 50)
    test_status_fix()
