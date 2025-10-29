# Como Usar o Google Automation Dashboard

## 🚀 Iniciar o Servidor

### ⚠️ IMPORTANTE: SEMPRE EM FOREGROUND

**NUNCA** execute o servidor em background (`&` ou `nohup`)!

### Método Correto (ÚNICO aceito)
```bash
python3 start_web.py
```

**Deixe o terminal aberto e rodando!** Você verá os logs em tempo real.

Este script:
- ✅ Verifica se a porta 5000 está em uso
- ✅ Mata processos anteriores automaticamente
- ✅ Abre o navegador automaticamente
- ✅ Previne servidores duplicados
- ✅ Roda em FOREGROUND (logs visíveis)

---

## 🛑 Parar o Servidor

### Se o servidor estiver travado ou duplicado:
```bash
./stop_server.sh
```

Ou manualmente:
```bash
lsof -ti:5000 | xargs kill -9
```

---

## 📱 Acessar a Aplicação

Após iniciar o servidor, acesse:

- **Home**: http://localhost:5000
- **Gmail**: http://localhost:5000/gmail
- **Google Sheets**: http://localhost:5000/sheets
- **Google Drive**: http://localhost:5000/drive

---

## ⚠️ Problemas Comuns

### "Address already in use"
**Causa**: Há outro servidor Flask rodando

**Solução**:
```bash
./stop_server.sh
python3 start_web.py
```

### Página não carrega (erro 401)
**Causa**: Cache do navegador

**Solução**:
- **Chrome/Edge**: `Ctrl + Shift + R` (Windows/Linux) ou `Cmd + Shift + R` (Mac)
- **Firefox**: `Ctrl + Shift + R` (Windows/Linux) ou `Cmd + Shift + R` (Mac)
- Ou abra em aba anônima/privada

### Credenciais expiradas
**Causa**: Token do Google expirou

**Solução**:
```bash
rm token.pickle
python3 start_web.py
```
Faça login novamente quando solicitado.

---

## 🎯 Funcionalidades do Gmail

### Filtros Rápidos
- **Todas**: Todas as mensagens da inbox
- **Não Lidas**: Apenas não lidas (padrão)
- **Com Estrela**: Mensagens com estrela
- **Importantes**: Mensagens importantes

### Ações por Mensagem
- 👁️ **Ver**: Visualiza conteúdo completo
- ↩️ **Responder**: Responde à mensagem
- 📦 **Arquivar**: Arquiva (remove da inbox)
- ✅ **Marcar lida/não lida**: Alterna status

### Busca Personalizada
Use a sintaxe do Gmail:
- `from:email@exemplo.com`
- `subject:reunião`
- `has:attachment`
- `is:important`

---

## 🔧 Comandos Úteis

### Verificar se o servidor está rodando:
```bash
curl http://localhost:5000/api/status
```

### Ver processos na porta 5000:
```bash
lsof -i:5000
```

### Matar processos Python:
```bash
pkill -9 python3
```

---

## 📝 Notas Importantes

1. **Sempre use `start_web.py`** para iniciar o servidor
2. **Não execute `app.py` diretamente** (use apenas para debug)
3. **Use `./stop_server.sh`** antes de reiniciar se houver problemas
4. O servidor **desabilita o reloader** para evitar problemas de memória
5. Credenciais são salvas em `token.pickle`

---

## 🆘 Suporte

Se encontrar problemas:
1. Execute `./stop_server.sh`
2. Delete `token.pickle` se houver problemas de autenticação
3. Execute `python3 start_web.py` novamente
4. Se persistir, reinicie o terminal
