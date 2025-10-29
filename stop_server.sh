#!/bin/bash
# Script para parar TODOS os servidores Flask em execução

echo "============================================"
echo "Parando todos os servidores Flask..."
echo "============================================"

# Remove o lock file se existir
LOCK_FILE="/tmp/painel_comando.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "Removendo lock file..."
    rm -f "$LOCK_FILE"
fi

# Mata todos os processos Python relacionados ao Flask
killall -9 python3 2>/dev/null
pkill -9 -f "flask run" 2>/dev/null
pkill -9 -f "app.py" 2>/dev/null
pkill -9 -f "start_web.py" 2>/dev/null

# Mata processos na porta 5000
lsof -ti:5000 | xargs -r kill -9 2>/dev/null

sleep 2

# Verifica se ainda há processos
FLASK_COUNT=$(ps aux | grep -E "(flask|app.py|start_web)" | grep -v grep | wc -l)
PORT_COUNT=$(lsof -ti:5000 2>/dev/null | wc -l)

if [ "$FLASK_COUNT" -eq 0 ] && [ "$PORT_COUNT" -eq 0 ]; then
    echo "✓ Todos os servidores foram parados com sucesso"
    echo "✓ Porta 5000 está livre"
else
    echo "⚠️  Alguns processos ainda estão rodando:"
    ps aux | grep -E "(flask|app.py|start_web)" | grep -v grep
fi

echo "============================================"
