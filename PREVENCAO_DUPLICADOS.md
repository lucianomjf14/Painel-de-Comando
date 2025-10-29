# 🛡️ Sistema de Prevenção de Servidores Duplicados

## ❌ O Problema

Múltiplos servidores Flask rodando simultaneamente causam:
- **Conflitos de memória** ("free(): invalid next size")
- **Porta 5000 bloqueada** ("Address already in use")
- **Crashes aleatórios** do servidor
- **Consumo excessivo de recursos**

---

## ✅ A Solução Implementada

### 1. **Lock File System**
O `start_web.py` agora usa um arquivo de lock (`/tmp/painel_comando.lock`) que:
- ✅ Contém o PID do processo rodando
- ✅ É verificado antes de iniciar nova instância
- ✅ É removido automaticamente ao encerrar
- ✅ Detecta locks obsoletos (processos mortos)

### 2. **Verificação de Porta**
Antes de iniciar, o script:
- ✅ Verifica se a porta 5000 está em uso
- ✅ Mata processos anteriores automaticamente
- ✅ Valida que a porta está livre

### 3. **Handlers de Limpeza**
Ao encerrar (Ctrl+C ou kill), o script:
- ✅ Remove o lock file
- ✅ Limpa recursos
- ✅ Encerra graciosamente

---

## 🎯 Como Usar Corretamente

### ✅ SEMPRE use este comando:
```bash
python3 start_web.py
```

### ❌ NUNCA execute diretamente:
```bash
# NÃO FAÇA ISSO:
python3 app.py                    # ❌
flask run                         # ❌
python3 -m flask run              # ❌
python3 app.py &                  # ❌ (background)
nohup python3 app.py &            # ❌ (background persistente)
```

---

## 🔒 Como Funciona a Proteção

### Tentativa 1: Tudo OK
```bash
$ python3 start_web.py
============================================================
Google Automation Dashboard - Iniciando...
============================================================
✓ Porta 5000 está livre
✓ Lock file criado (PID: 12345)
🚀 Servidor iniciando...
```

### Tentativa 2: Proteção Ativa
```bash
$ python3 start_web.py
============================================================
Google Automation Dashboard - Iniciando...
============================================================

❌ ERRO: Já existe uma instância rodando (PID: 12345)

Para parar o servidor anterior, execute:
  kill 12345
  ou
  ./stop_server.sh
============================================================
```

---

## 🛑 Em Caso de Emergência

### Se tudo der errado:
```bash
./stop_server.sh
```

Este script:
1. Remove o lock file
2. Mata TODOS os processos Flask
3. Libera a porta 5000
4. Verifica que tudo foi parado

---

## 📊 Verificar Status

### Ver se há servidor rodando:
```bash
cat /tmp/painel_comando.lock
# Mostra o PID se estiver rodando
```

### Ver processos Flask:
```bash
ps aux | grep -E "(flask|app.py|start_web)"
```

### Ver o que está na porta 5000:
```bash
lsof -i:5000
```

---

## 🔍 Diagnóstico

### Lock file existe mas servidor não roda?
```bash
rm /tmp/painel_comando.lock
python3 start_web.py
```

### Servidor travou e não responde?
```bash
./stop_server.sh
python3 start_web.py
```

### Erro "Address already in use"?
```bash
lsof -ti:5000 | xargs kill -9
rm /tmp/painel_comando.lock
python3 start_web.py
```

---

## 📝 Regras de Ouro

1. ✅ **SEMPRE** use `python3 start_web.py`
2. ✅ **SEMPRE** use `./stop_server.sh` para parar
3. ❌ **NUNCA** execute múltiplas instâncias manualmente
4. ❌ **NUNCA** execute `app.py` diretamente
5. ✅ **SEMPRE** verifique com `lsof -i:5000` antes de iniciar manualmente

---

## 🎓 Para Desenvolvedores

Se você está desenvolvendo e precisa reiniciar frequentemente:

```bash
# Alias útil no ~/.bashrc ou ~/.zshrc
alias start-painel="./stop_server.sh && python3 start_web.py"
alias stop-painel="./stop_server.sh"
alias status-painel="lsof -i:5000 && cat /tmp/painel_comando.lock 2>/dev/null || echo 'Nenhum servidor rodando'"
```

---

## 🚨 Garantias do Sistema

O sistema garante que:
- ✅ **Apenas 1 instância** pode rodar por vez
- ✅ **Lock file é sempre removido** ao encerrar
- ✅ **Locks obsoletos são detectados** e removidos
- ✅ **Porta é verificada** antes de iniciar
- ✅ **Processos anteriores são mortos** automaticamente

---

## ⚙️ Arquivos do Sistema

- **Lock File**: `/tmp/painel_comando.lock`
- **Startup**: `start_web.py`
- **Cleanup**: `stop_server.sh`
- **Porta**: `5000`

---

**Última atualização**: 28/10/2025
**Versão**: 2.0 (com proteção contra duplicados)
