#!/bin/bash

echo "==================================================="
echo "Iniciando Painel de Comando (Safe Mode)"
echo "==================================================="

# Mata qualquer processo Python anterior
echo "Verificando processos anteriores..."
pkill -9 -f "python.*start_web.py" 2>/dev/null
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 2

# Verifica se a porta 5000 está em uso
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Porta 5000 está em uso. Liberando..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Define variáveis de ambiente para otimização
export PYTHONUNBUFFERED=1
export MALLOC_CHECK_=0  # Desabilita verificações de memória que podem causar double free

# Limpa cache de Python
echo "Limpando cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "Iniciando servidor..."
echo "==================================================="

# Inicia a aplicação
cd /workspaces/Painel-de-Comando
python3 start_web.py
