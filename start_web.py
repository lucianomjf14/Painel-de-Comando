#!/usr/bin/env python3
"""
Script para iniciar a aplicação web Painel de Comando
com proteção contra múltiplas instâncias
"""

import os
import sys
import webbrowser
import time
import socket
import subprocess
import atexit
import signal
from threading import Timer

# Arquivo de lock para prevenir múltiplas instâncias
LOCK_FILE = '/tmp/painel_comando.lock'

def check_port_in_use(port):
    """Verifica se a porta está em uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_processes_on_port(port):
    """Mata processos rodando na porta especificada"""
    try:
        # Usa lsof para encontrar processos na porta
        result = subprocess.run(['lsof', '-ti', f':{port}'],
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                print(f"  Matando processo {pid} na porta {port}...")
                subprocess.run(['kill', '-9', pid], stderr=subprocess.DEVNULL)
            time.sleep(1)
            return True
        return False
    except Exception as e:
        print(f"  Erro ao tentar matar processos: {e}")
        return False

def create_lock_file():
    """Cria arquivo de lock com PID"""
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_lock_file():
    """Remove arquivo de lock"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            print("\nLock file removido")
    except Exception as e:
        print(f"Aviso: Erro ao remover lock file: {e}")

def check_lock_file():
    """Verifica se já existe uma instância rodando"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            # Verifica se o processo ainda existe
            try:
                os.kill(old_pid, 0)  # Signal 0 apenas verifica se existe
                return True, old_pid
            except OSError:
                # Processo não existe mais, remove lock obsoleto
                os.remove(LOCK_FILE)
                return False, None
        except:
            # Lock file corrompido, remove
            os.remove(LOCK_FILE)
            return False, None
    return False, None

def signal_handler(signum, frame):
    """Handler para sinais de interrupção"""
    print("\n\nSinal de interrupção recebido...")
    remove_lock_file()
    sys.exit(0)

def open_browser():
    """Abre o navegador após 2 segundos"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    PORT = 5000

    # Registra handlers de limpeza
    atexit.register(remove_lock_file)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("Painel de Comando - Iniciando...")
    print("=" * 60)

    # PROTEÇÃO CONTRA MÚLTIPLAS INSTÂNCIAS
    is_running, old_pid = check_lock_file()
    if is_running:
        print(f"\nERRO: Já existe uma instância rodando (PID: {old_pid})")
        print(f"\nPara parar o servidor anterior, execute:")
        print(f"  kill {old_pid}")
        print(f"  ou")
        print(f"  ./stop_server.sh")
        print("\n" + "=" * 60)
        sys.exit(1)

    # Verifica se a porta está em uso
    if check_port_in_use(PORT):
        print(f"\nAVISO: Porta {PORT} já está em uso!")
        print("Tentando encerrar processos anteriores...")

        if kill_processes_on_port(PORT):
            print("Processos anteriores encerrados")
            time.sleep(2)
        else:
            print(f"\nERRO: Não foi possível liberar a porta {PORT}")
            print(f"Execute manualmente: lsof -ti:{PORT} | xargs kill -9")
            sys.exit(1)

    # Verifica novamente após tentar matar
    if check_port_in_use(PORT):
        print(f"\nERRO: Porta {PORT} ainda está em uso!")
        print("Por favor, encerre manualmente todos os processos Flask")
        sys.exit(1)

    print(f"\nPorta {PORT} está livre")
    print("\nEndpoints disponíveis:")
    print(f"  • Gmail:  http://localhost:{PORT}/gmail")
    print(f"  • Sheets: http://localhost:{PORT}/sheets")
    print(f"  • Drive:  http://localhost:{PORT}/drive")
    print(f"  • Home:   http://localhost:{PORT}")
    print("=" * 60)
    print("\nAguarde... O navegador será aberto automaticamente")
    print("Pressione Ctrl+C para encerrar o servidor")
    print("=" * 60)

    # Cria o arquivo de lock
    create_lock_file()
    print(f"Lock file criado (PID: {os.getpid()})")

    # Abre o navegador após 3 segundos
    Timer(3.0, open_browser).start()

    # Importa e executa a aplicação Flask
    try:
        from app import app
        print(f"\nServidor iniciando na porta {PORT}...")
        print("=" * 60)
        # Desabilita reloader para evitar problemas de memória
        app.run(
            debug=False,
            host='0.0.0.0',
            port=PORT,
            use_reloader=False,
            threaded=False
        )
    except ImportError as e:
        print(f"\nErro ao importar a aplicacao: {e}")
        print("Certifique-se de que todas as dependencias estao instaladas:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nERRO: Porta {PORT} está em uso por outro processo")
            print(f"Execute: lsof -ti:{PORT} | xargs kill -9")
        else:
            print(f"\nErro de sistema: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nServidor encerrado pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro ao iniciar a aplicacao: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
