# Guia de Uso Rápido - Google Sheets & Drive Automation

## 🚀 Início Rápido

### 1. Instalação
```bash
python setup.py
```

### 2. Configurar Credenciais
1. Baixe `credentials.json` do Google Cloud Console
2. Coloque na raiz do projeto
3. Execute: `python cli.py auth login`

### 3. Testar
```bash
python exemplo.py
```

## 📋 Comandos Principais

### Google Sheets
```bash
# Criar planilha
python cli.py sheets create --title "Nova Planilha"

# Ler dados
python cli.py sheets read --spreadsheet-id "ID" --range "A1:C10"

# Escrever dados
python cli.py sheets write --spreadsheet-id "ID" --range "A1:C3" --data "dados.csv"

# Informações da planilha
python cli.py sheets info --spreadsheet-id "ID"
```

### Google Drive
```bash
# Listar arquivos
python cli.py drive list

# Buscar arquivo
python cli.py drive search --name "planilha"

# Upload
python cli.py drive upload --file "arquivo.xlsx"

# Download
python cli.py drive download --file-id "ID" --output "arquivo.xlsx"

# Criar pasta
python cli.py drive create-folder --name "Nova Pasta"
```

## 🔧 Uso Programático

```python
from sheets.sheets_manager import GoogleSheetsManager
from drive.drive_manager import GoogleDriveManager

# Sheets
sheets = GoogleSheetsManager()
spreadsheet_id = sheets.create_spreadsheet("Minha Planilha")
sheets.write_to_spreadsheet(spreadsheet_id, "A1:C3", dados)

# Drive
drive = GoogleDriveManager()
file_id = drive.upload_file("arquivo.xlsx")
files = drive.list_files()
```

## 📁 Estrutura de Arquivos

```
projeto/
├── auth/                    # Autenticação
├── sheets/                  # Google Sheets
├── drive/                   # Google Drive
├── cli.py                   # Interface CLI
├── exemplo.py               # Exemplos
├── setup.py                 # Instalação
└── requirements.txt         # Dependências
```

## ⚠️ Importante

- Mantenha `credentials.json` seguro
- Não commite credenciais no Git
- Use `.env` para configurações sensíveis
- Teste sempre em ambiente de desenvolvimento primeiro
