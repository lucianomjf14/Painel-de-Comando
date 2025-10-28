import pandas as pd
import json
from typing import List, Dict, Any, Optional
from auth.google_auth import google_auth
from config import DEFAULT_SHEET_NAME, DEFAULT_RANGE


class GoogleSheetsManager:
    """Classe para gerenciar operações no Google Sheets"""
    
    def __init__(self):
        self.service = google_auth.get_sheets_service()
    
    def list_spreadsheets(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Lista planilhas do usuário"""
        try:
            # Nota: A API do Sheets não tem um método direto para listar planilhas
            # Isso seria feito através da API do Drive
            print("Para listar planilhas, use o comando 'drive list' com filtro para arquivos .xlsx/.gsheet")
            return []
        except Exception as e:
            print(f"Erro ao listar planilhas: {e}")
            return []
    
    def read_spreadsheet(self, spreadsheet_id: str, range_name: str = None) -> pd.DataFrame:
        """Lê dados de uma planilha"""
        try:
            if not range_name:
                range_name = DEFAULT_RANGE
            
            # Adiciona o nome da planilha se não especificado
            if '!' not in range_name:
                range_name = f"{DEFAULT_SHEET_NAME}!{range_name}"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("Nenhum dado encontrado na planilha.")
                return pd.DataFrame()
            
            # Converte para DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
            
        except Exception as e:
            print(f"Erro ao ler planilha: {e}")
            return pd.DataFrame()
    
    def write_to_spreadsheet(self, spreadsheet_id: str, range_name: str, data: Any) -> bool:
        """Escreve dados em uma planilha"""
        try:
            # Adiciona o nome da planilha se não especificado
            if '!' not in range_name:
                range_name = f"{DEFAULT_SHEET_NAME}!{range_name}"
            
            # Converte dados para o formato esperado
            if isinstance(data, pd.DataFrame):
                values = [data.columns.tolist()] + data.values.tolist()
            elif isinstance(data, str) and data.endswith('.csv'):
                df = pd.read_csv(data)
                values = [df.columns.tolist()] + df.values.tolist()
            elif isinstance(data, list):
                values = data
            else:
                print("Formato de dados não suportado")
                return False
            
            body = {'values': values}
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"Dados escritos com sucesso! {result.get('updatedCells')} células atualizadas.")
            return True
            
        except Exception as e:
            print(f"Erro ao escrever na planilha: {e}")
            return False
    
    def create_spreadsheet(self, title: str) -> Optional[str]:
        """Cria uma nova planilha"""
        try:
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }
            
            request = self.service.spreadsheets().create(body=spreadsheet_body)
            response = request.execute()
            
            spreadsheet_id = response['spreadsheetId']
            print(f"Planilha '{title}' criada com sucesso!")
            print(f"ID: {spreadsheet_id}")
            print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            
            return spreadsheet_id
            
        except Exception as e:
            print(f"Erro ao criar planilha: {e}")
            return None
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Obtém informações sobre uma planilha"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            info = {
                'title': spreadsheet['properties']['title'],
                'sheets': [sheet['properties']['title'] for sheet in spreadsheet['sheets']],
                'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            }
            
            return info
            
        except Exception as e:
            print(f"Erro ao obter informações da planilha: {e}")
            return {}
    
    def add_sheet(self, spreadsheet_id: str, sheet_name: str) -> bool:
        """Adiciona uma nova aba à planilha"""
        try:
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            print(f"Aba '{sheet_name}' adicionada com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar aba: {e}")
            return False
    
    def clear_range(self, spreadsheet_id: str, range_name: str) -> bool:
        """Limpa o conteúdo de um intervalo"""
        try:
            # Adiciona o nome da planilha se não especificado
            if '!' not in range_name:
                range_name = f"{DEFAULT_SHEET_NAME}!{range_name}"
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            print(f"Intervalo '{range_name}' limpo com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao limpar intervalo: {e}")
            return False
