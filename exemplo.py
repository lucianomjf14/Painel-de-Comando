#!/usr/bin/env python3
"""
Script de exemplo para demonstrar o uso da automação do Google Sheets e Drive
"""

import pandas as pd
from sheets.sheets_manager import GoogleSheetsManager
from drive.drive_manager import GoogleDriveManager
from gmail.gmail_manager import GmailManager


def exemplo_completo():
    """Exemplo completo de uso das APIs"""
    
    print("=== Exemplo de Automação Google Sheets e Drive ===\n")
    
    # Inicializa os gerenciadores
    sheets_manager = GoogleSheetsManager()
    drive_manager = GoogleDriveManager()
    gmail_manager = GmailManager()
    
    # 1. Criar uma nova planilha
    print("1. Criando nova planilha...")
    spreadsheet_id = sheets_manager.create_spreadsheet("Planilha de Teste - Automação")
    
    if spreadsheet_id:
        # 2. Criar dados de exemplo
        print("\n2. Criando dados de exemplo...")
        dados = {
            'Nome': ['João', 'Maria', 'Pedro', 'Ana'],
            'Idade': [25, 30, 35, 28],
            'Cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador'],
            'Salário': [5000, 6000, 7000, 5500]
        }
        df = pd.DataFrame(dados)
        
        # 3. Escrever dados na planilha
        print("\n3. Escrevendo dados na planilha...")
        sheets_manager.write_to_spreadsheet(spreadsheet_id, "A1:D5", df)
        
        # 4. Ler dados da planilha
        print("\n4. Lendo dados da planilha...")
        dados_lidos = sheets_manager.read_spreadsheet(spreadsheet_id, "A1:D5")
        print(dados_lidos)
        
        # 5. Salvar dados em CSV local
        print("\n5. Salvando dados em CSV local...")
        df.to_csv('dados_exemplo.csv', index=False)
        
        # 6. Fazer upload do CSV para o Drive
        print("\n6. Fazendo upload do CSV para o Google Drive...")
        file_id = drive_manager.upload_file('dados_exemplo.csv', name='dados_exemplo_upload.csv')
        
        # 7. Listar arquivos do Drive
        print("\n7. Listando arquivos do Google Drive...")
        files = drive_manager.list_files(max_results=5)
        for file in files:
            print(f"- {file['name']} ({file['id']})")
        
        print(f"\n=== Exemplo concluído! ===")
        print(f"Planilha criada: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        if file_id:
            print(f"Arquivo no Drive: https://drive.google.com/file/d/{file_id}/view")


def exemplo_planilhas():
    """Exemplo específico para Google Sheets"""
    
    print("=== Exemplo Google Sheets ===\n")
    
    sheets_manager = GoogleSheetsManager()
    
    # Criar planilha
    spreadsheet_id = sheets_manager.create_spreadsheet("Relatório de Vendas")
    
    if spreadsheet_id:
        # Dados de vendas
        vendas = {
            'Produto': ['Notebook', 'Mouse', 'Teclado', 'Monitor'],
            'Quantidade': [10, 50, 30, 15],
            'Preço Unitário': [2500, 50, 150, 800],
            'Total': [25000, 2500, 4500, 12000]
        }
        
        df_vendas = pd.DataFrame(vendas)
        
        # Escrever dados
        sheets_manager.write_to_spreadsheet(spreadsheet_id, "A1:D5", df_vendas)
        
        # Adicionar nova aba
        sheets_manager.add_sheet(spreadsheet_id, "Resumo")
        
        # Dados de resumo
        resumo = {
            'Métrica': ['Total de Produtos', 'Valor Total', 'Ticket Médio'],
            'Valor': [105, 44000, 419]
        }
        
        df_resumo = pd.DataFrame(resumo)
        sheets_manager.write_to_spreadsheet(spreadsheet_id, "Resumo!A1:B4", df_resumo)
        
        print(f"Planilha de vendas criada: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


def exemplo_drive():
    """Exemplo específico para Google Drive"""
    
    print("=== Exemplo Google Drive ===\n")
    
    drive_manager = GoogleDriveManager()
    
    # Criar pasta
    folder_id = drive_manager.create_folder("Projetos 2024")
    
    if folder_id:
        # Criar subpasta
        subfolder_id = drive_manager.create_folder("Relatórios", folder_id)
        
        # Criar arquivo de exemplo
        with open('relatorio_exemplo.txt', 'w', encoding='utf-8') as f:
            f.write("Relatório de Exemplo\n\n")
            f.write("Este é um relatório gerado automaticamente.\n")
            f.write("Data: 2024\n")
            f.write("Status: Concluído\n")
        
        # Upload para a subpasta
        file_id = drive_manager.upload_file('relatorio_exemplo.txt', subfolder_id)
        
        # Buscar arquivos
        files = drive_manager.search_files("relatorio")
        
        print("Arquivos encontrados:")
        for file in files:
            print(f"- {file['name']} ({file['id']})")


def exemplo_gmail():
    """Exemplo específico para Gmail"""
    
    print("=== Exemplo Gmail ===\n")
    
    gmail_manager = GmailManager()
    
    # Listar mensagens não lidas
    print("1. Listando mensagens não lidas...")
    unread_messages = gmail_manager.list_messages("is:unread", 5)
    
    if unread_messages:
        print(f"Encontradas {len(unread_messages)} mensagens não lidas:")
        for msg in unread_messages:
            print(f"- {msg['subject']} (de: {msg['sender']})")
    else:
        print("Nenhuma mensagem não lida encontrada.")
    
    # Contar mensagens não lidas
    print(f"\n2. Total de mensagens não lidas: {gmail_manager.get_unread_count()}")
    
    # Listar labels
    print("\n3. Labels disponíveis:")
    labels = gmail_manager.get_labels()
    for label in labels[:5]:  # Mostrar apenas os primeiros 5
        print(f"- {label['name']}")
    
    # Buscar mensagens de um remetente específico
    print("\n4. Buscando mensagens recentes...")
    recent_messages = gmail_manager.search_messages("in:inbox", 3)
    
    if recent_messages:
        print("Mensagens recentes:")
        for msg in recent_messages:
            print(f"- {msg['subject']} (de: {msg['sender']})")
    
    # Exemplo de envio de email (comentado para não enviar emails reais)
    print("\n5. Exemplo de envio de email (comentado):")
    print("# gmail_manager.send_email(")
    print("#     to='exemplo@gmail.com',")
    print("#     subject='Teste de Automação',")
    print("#     body='Este é um email de teste enviado automaticamente!'")
    print("# )")


if __name__ == "__main__":
    try:
        # Executa exemplo completo
        exemplo_completo()
        
        print("\n" + "="*50 + "\n")
        
        # Exemplos específicos
        exemplo_planilhas()
        
        print("\n" + "="*50 + "\n")
        
        exemplo_drive()
        
        print("\n" + "="*50 + "\n")
        
        exemplo_gmail()
        
    except Exception as e:
        print(f"Erro durante execução: {e}")
        print("Certifique-se de que:")
        print("1. As credenciais estão configuradas (credentials.json)")
        print("2. As dependências estão instaladas (pip install -r requirements.txt)")
        print("3. Você fez login (python cli.py auth login)")
