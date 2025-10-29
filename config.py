import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Google API
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
SCOPES = os.getenv('SCOPES', 'openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.compose,https://www.googleapis.com/auth/gmail.readonly').split(',')
TOKEN_FILE = os.getenv('TOKEN_FILE', 'token.pickle')

# Configurações padrão
DEFAULT_SHEET_NAME = 'Sheet1'
DEFAULT_RANGE = 'A1:Z1000'
MAX_RESULTS = 100
