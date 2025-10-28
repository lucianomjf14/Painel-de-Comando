# Google Sheets, Drive & Gmail Automation

Este projeto fornece uma infraestrutura completa para automação do Google Sheets, Google Drive e Gmail via terminal.

## Configuração Inicial

### 1. Configurar Credenciais do Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative as APIs necessárias:
   - Google Sheets API
   - Google Drive API
   - Gmail API
4. Crie credenciais OAuth 2.0:
   - Tipo: Aplicação Desktop
   - Baixe o arquivo JSON das credenciais
5. Renomeie o arquivo para `credentials.json` e coloque na raiz do projeto

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
SCOPES=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.compose,https://www.googleapis.com/auth/gmail.readonly
```

## Uso

### 🌐 Interface Web (Recomendado)

Para uma experiência mais amigável, use a interface web:

```bash
# Iniciar aplicação web
python start_web.py
```

Acesse `http://localhost:5000` no seu navegador para:
- 📧 **Gmail**: Visualizar, enviar e organizar emails
- 📊 **Sheets**: Criar, editar e gerenciar planilhas  
- 💾 **Drive**: Upload, download e organizar arquivos
- 📱 **Interface responsiva** para desktop e mobile

### 💻 Linha de Comando

#### Automação do Google Sheets

```bash
# Listar planilhas
python cli.py sheets list

# Ler dados de uma planilha
python cli.py sheets read --spreadsheet-id "ID_DA_PLANILHA" --range "A1:C10"

# Escrever dados em uma planilha
python cli.py sheets write --spreadsheet-id "ID_DA_PLANILHA" --range "A1:C3" --data "dados.csv"

# Criar nova planilha
python cli.py sheets create --title "Nova Planilha"
```

### Automação do Google Drive

```bash
# Listar arquivos
python cli.py drive list

# Fazer upload de arquivo
python cli.py drive upload --file "arquivo.xlsx" --folder-id "ID_DA_PASTA"

# Fazer download de arquivo
python cli.py drive download --file-id "ID_DO_ARQUIVO" --output "arquivo_local.xlsx"

# Criar pasta
python cli.py drive create-folder --name "Nova Pasta"
```

### Automação do Gmail

```bash
# Listar mensagens
python cli.py gmail list

# Listar mensagens não lidas
python cli.py gmail list --query "is:unread"

# Ler uma mensagem específica
python cli.py gmail read --message-id "ID_DA_MENSAGEM"

# Enviar email
python cli.py gmail send --to "destinatario@gmail.com" --subject "Assunto" --body "Corpo da mensagem"

# Enviar email HTML
python cli.py gmail send-html --to "destinatario@gmail.com" --subject "Assunto" --html-file "email.html"

# Responder mensagem
python cli.py gmail reply --message-id "ID_DA_MENSAGEM" --reply-text "Texto da resposta"

# Encaminhar mensagem
python cli.py gmail forward --message-id "ID_DA_MENSAGEM" --to "destinatario@gmail.com"

# Marcar como lida
python cli.py gmail mark-read --message-id "ID_DA_MENSAGEM"

# Adicionar label
python cli.py gmail add-label --message-id "ID_DA_MENSAGEM" --label-name "Importante"

# Buscar mensagens
python cli.py gmail search --query "from:exemplo@gmail.com"

# Contar não lidas
python cli.py gmail unread-count

# Listar labels
python cli.py gmail labels

# Criar label
python cli.py gmail create-label --name "Novo Label"
```

## Instalação Rápida

Execute o script de instalação automática:

```bash
python setup.py
```

Este script irá:
- Instalar todas as dependências necessárias
- Verificar se as credenciais estão configuradas
- Criar arquivos de configuração
- Testar a conexão com as APIs

## Estrutura do Projeto

```
├── auth/                    # Módulos de autenticação
│   ├── __init__.py
│   └── google_auth.py
├── sheets/                  # Módulos para Google Sheets
│   ├── __init__.py
│   └── sheets_manager.py
├── drive/                   # Módulos para Google Drive
│   ├── __init__.py
│   └── drive_manager.py
├── gmail/                   # Módulos para Gmail
│   ├── __init__.py
│   └── gmail_manager.py
├── cli.py                  # Interface de linha de comando
├── config.py               # Configurações do projeto
├── exemplo.py              # Scripts de exemplo
├── setup.py                # Script de instalação
├── requirements.txt        # Dependências Python
├── credentials.json.example # Exemplo de credenciais
└── README.md               # Este arquivo
```

## Exemplos de Uso

### Script de Exemplo Completo
```bash
python exemplo.py
```

### Comandos Úteis

```bash
# Fazer login
python cli.py auth login

# Listar arquivos do Drive
python cli.py drive list

# Criar nova planilha
python cli.py sheets create --title "Minha Planilha"

# Ler dados de uma planilha
python cli.py sheets read --spreadsheet-id "ID_DA_PLANILHA" --range "A1:C10"

# Fazer upload de arquivo
python cli.py drive upload --file "arquivo.xlsx"
```

## Troubleshooting

### Problemas Comuns

1. **Erro de credenciais**: Certifique-se de que o arquivo `credentials.json` está na raiz do projeto
2. **Erro de permissões**: Execute `python cli.py auth login` para renovar as credenciais
3. **Dependências não instaladas**: Execute `pip install -r requirements.txt`

### Logs e Debug

Para ver logs detalhados, adicione `--verbose` aos comandos quando disponível.
