#!/usr/bin/env python3
"""
Interface de linha de comando para automação do Google Sheets e Google Drive
"""

import click
import pandas as pd
from sheets.sheets_manager import GoogleSheetsManager
from drive.drive_manager import GoogleDriveManager
from gmail.gmail_manager import GmailManager
from auth.google_auth import google_auth


@click.group()
def cli():
    """Ferramenta de automação para Google Sheets e Google Drive"""
    pass


@cli.group()
def sheets():
    """Comandos para manipulação do Google Sheets"""
    pass


@cli.group()
def drive():
    """Comandos para manipulação do Google Drive"""
    pass


@cli.group()
def gmail():
    """Comandos para manipulação do Gmail"""
    pass


@cli.group()
def auth():
    """Comandos de autenticação"""
    pass


# Comandos do Google Sheets
@sheets.command()
def list():
    """Lista planilhas disponíveis"""
    sheets_manager = GoogleSheetsManager()
    sheets_manager.list_spreadsheets()


@sheets.command()
@click.option('--spreadsheet-id', required=True, help='ID da planilha')
@click.option('--range', default='A1:Z1000', help='Intervalo a ser lido (ex: A1:C10)')
@click.option('--output', help='Arquivo de saída (CSV)')
def read(spreadsheet_id, range, output):
    """Lê dados de uma planilha"""
    sheets_manager = GoogleSheetsManager()
    df = sheets_manager.read_spreadsheet(spreadsheet_id, range)
    
    if not df.empty:
        if output:
            df.to_csv(output, index=False)
            print(f"Dados salvos em: {output}")
        else:
            print(df.to_string())


@sheets.command()
@click.option('--spreadsheet-id', required=True, help='ID da planilha')
@click.option('--range', required=True, help='Intervalo a ser escrito (ex: A1:C3)')
@click.option('--data', required=True, help='Arquivo CSV com os dados ou dados em formato JSON')
def write(spreadsheet_id, range, data):
    """Escreve dados em uma planilha"""
    sheets_manager = GoogleSheetsManager()
    sheets_manager.write_to_spreadsheet(spreadsheet_id, range, data)


@sheets.command()
@click.option('--title', required=True, help='Título da nova planilha')
def create(title):
    """Cria uma nova planilha"""
    sheets_manager = GoogleSheetsManager()
    sheets_manager.create_spreadsheet(title)


@sheets.command()
@click.option('--spreadsheet-id', required=True, help='ID da planilha')
def info(spreadsheet_id):
    """Mostra informações sobre uma planilha"""
    sheets_manager = GoogleSheetsManager()
    info = sheets_manager.get_spreadsheet_info(spreadsheet_id)
    
    if info:
        print(f"Título: {info['title']}")
        print(f"URL: {info['url']}")
        print(f"Abas: {', '.join(info['sheets'])}")


@sheets.command()
@click.option('--spreadsheet-id', required=True, help='ID da planilha')
@click.option('--sheet-name', required=True, help='Nome da nova aba')
def add_sheet(spreadsheet_id, sheet_name):
    """Adiciona uma nova aba à planilha"""
    sheets_manager = GoogleSheetsManager()
    sheets_manager.add_sheet(spreadsheet_id, sheet_name)


@sheets.command()
@click.option('--spreadsheet-id', required=True, help='ID da planilha')
@click.option('--range', required=True, help='Intervalo a ser limpo (ex: A1:C10)')
def clear(spreadsheet_id, range):
    """Limpa o conteúdo de um intervalo"""
    sheets_manager = GoogleSheetsManager()
    sheets_manager.clear_range(spreadsheet_id, range)


# Comandos do Google Drive
@drive.command()
@click.option('--query', help='Query de busca (ex: "name contains \'planilha\'")')
@click.option('--max-results', default=10, help='Número máximo de resultados')
def list(query, max_results):
    """Lista arquivos do Google Drive"""
    drive_manager = GoogleDriveManager()
    files = drive_manager.list_files(query, max_results)
    
    if files:
        print(f"{'Nome':<30} {'Tipo':<20} {'ID':<30} {'Modificado':<20}")
        print("-" * 100)
        for file in files:
            name = file['name'][:29] if len(file['name']) > 29 else file['name']
            mime_type = file.get('mimeType', 'N/A')[:19] if file.get('mimeType') else 'N/A'
            file_id = file['id']
            modified = file.get('modifiedTime', 'N/A')[:19] if file.get('modifiedTime') else 'N/A'
            print(f"{name:<30} {mime_type:<20} {file_id:<30} {modified:<20}")


@drive.command()
@click.option('--name', required=True, help='Nome do arquivo a ser buscado')
@click.option('--mime-type', help='Tipo MIME do arquivo')
def search(name, mime_type):
    """Busca arquivos por nome"""
    drive_manager = GoogleDriveManager()
    files = drive_manager.search_files(name, mime_type)
    
    if files:
        for file in files:
            print(f"Nome: {file['name']}")
            print(f"ID: {file['id']}")
            print(f"Tipo: {file.get('mimeType', 'N/A')}")
            print(f"Modificado: {file.get('modifiedTime', 'N/A')}")
            print("-" * 50)


@drive.command()
@click.option('--file', required=True, help='Caminho do arquivo local')
@click.option('--folder-id', help='ID da pasta de destino')
@click.option('--name', help='Nome do arquivo no Drive')
def upload(file, folder_id, name):
    """Faz upload de um arquivo para o Google Drive"""
    drive_manager = GoogleDriveManager()
    drive_manager.upload_file(file, folder_id, name)


@drive.command()
@click.option('--file-id', required=True, help='ID do arquivo no Drive')
@click.option('--output', help='Caminho do arquivo de saída')
def download(file_id, output):
    """Faz download de um arquivo do Google Drive"""
    drive_manager = GoogleDriveManager()
    drive_manager.download_file(file_id, output)


@drive.command()
@click.option('--name', required=True, help='Nome da nova pasta')
@click.option('--parent-folder-id', help='ID da pasta pai')
def create_folder(name, parent_folder_id):
    """Cria uma nova pasta no Google Drive"""
    drive_manager = GoogleDriveManager()
    drive_manager.create_folder(name, parent_folder_id)


@drive.command()
@click.option('--file-id', required=True, help='ID do arquivo')
@click.option('--permanent', is_flag=True, help='Exclusão permanente (não vai para lixeira)')
def delete(file_id, permanent):
    """Exclui um arquivo do Google Drive"""
    drive_manager = GoogleDriveManager()
    drive_manager.delete_file(file_id, permanent)


@drive.command()
@click.option('--file-id', required=True, help='ID do arquivo')
def info(file_id):
    """Mostra informações detalhadas de um arquivo"""
    drive_manager = GoogleDriveManager()
    info = drive_manager.get_file_info(file_id)
    
    if info:
        print(f"Nome: {info.get('name', 'N/A')}")
        print(f"ID: {info.get('id', 'N/A')}")
        print(f"Tipo: {info.get('mimeType', 'N/A')}")
        print(f"Tamanho: {info.get('size', 'N/A')} bytes")
        print(f"Criado: {info.get('createdTime', 'N/A')}")
        print(f"Modificado: {info.get('modifiedTime', 'N/A')}")
        print(f"URL: {info.get('webViewLink', 'N/A')}")


@drive.command()
@click.option('--file-id', required=True, help='ID do arquivo a ser copiado')
@click.option('--new-name', help='Nome da cópia')
@click.option('--folder-id', help='ID da pasta de destino')
def copy(file_id, new_name, folder_id):
    """Cria uma cópia de um arquivo"""
    drive_manager = GoogleDriveManager()
    drive_manager.copy_file(file_id, new_name, folder_id)


@drive.command()
@click.option('--file-id', required=True, help='ID do arquivo')
@click.option('--folder-id', required=True, help='ID da pasta de destino')
def move(file_id, folder_id):
    """Move um arquivo para outra pasta"""
    drive_manager = GoogleDriveManager()
    drive_manager.move_file(file_id, folder_id)


# Comandos de autenticação
@auth.command()
def login():
    """Realiza login nas APIs do Google"""
    try:
        google_auth.authenticate()
        print("Login realizado com sucesso!")
    except Exception as e:
        print(f"Erro no login: {e}")


@auth.command()
def logout():
    """Revoga as credenciais salvas"""
    google_auth.revoke_credentials()


# Comandos do Gmail
@gmail.command()
@click.option('--query', help='Query de busca (ex: "is:unread from:exemplo@gmail.com")')
@click.option('--max-results', default=10, help='Número máximo de resultados')
def list(query, max_results):
    """Lista mensagens do Gmail"""
    gmail_manager = GmailManager()
    result = gmail_manager.list_messages(query, max_results)
    messages = result.get('messages', [])
    next_token = result.get('next_page_token')
    
    if messages:
        print(f"{'Assunto':<50} {'Remetente':<30} {'Data':<20} {'ID':<30}")
        print("-" * 130)
        for msg in messages:
            subject = msg['subject'][:49] if len(msg['subject']) > 49 else msg['subject']
            sender = msg['sender'][:29] if len(msg['sender']) > 29 else msg['sender']
            date = msg['date'][:19] if len(msg['date']) > 19 else msg['date']
            print(f"{subject:<50} {sender:<30} {date:<20} {msg['id']:<30}")
        estimated_total = result.get('estimated_total')
        if estimated_total is not None:
            print(f"\nEstimativa total de mensagens para a busca: {estimated_total}")
        if next_token:
            print("\nMais resultados disponíveis. Use --max-results e --query com page_token:")
            print(next_token)
    else:
        print("Nenhuma mensagem encontrada.")


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
def read(message_id):
    """Lê uma mensagem específica"""
    gmail_manager = GmailManager()
    message = gmail_manager.get_message(message_id)
    
    if message:
        print(f"Assunto: {message['subject']}")
        print(f"De: {message['sender']}")
        print(f"Para: {message['recipient']}")
        print(f"Data: {message['date']}")
        print(f"ID: {message['id']}")
        print("\nCorpo da mensagem:")
        print("-" * 50)
        print(message['body'])
        
        if message['attachments']:
            print(f"\nAnexos ({len(message['attachments'])}):")
            for att in message['attachments']:
                print(f"- {att['filename']} ({att['mimeType']}) - {att['size']} bytes")
    else:
        print("Mensagem não encontrada.")


@gmail.command()
@click.option('--to', required=True, help='Destinatário')
@click.option('--subject', required=True, help='Assunto')
@click.option('--body', required=True, help='Corpo da mensagem')
@click.option('--cc', help='Cópia')
@click.option('--bcc', help='Cópia oculta')
@click.option('--attachments', help='Anexos (separados por vírgula)')
def send(to, subject, body, cc, bcc, attachments):
    """Envia um email"""
    gmail_manager = GmailManager()
    
    att_list = None
    if attachments:
        att_list = [att.strip() for att in attachments.split(',')]
    
    gmail_manager.send_email(to, subject, body, cc, bcc, att_list)


@gmail.command()
@click.option('--to', required=True, help='Destinatário')
@click.option('--subject', required=True, help='Assunto')
@click.option('--html-file', required=True, help='Arquivo HTML com o corpo do email')
@click.option('--cc', help='Cópia')
@click.option('--bcc', help='Cópia oculta')
def send_html(to, subject, html_file, cc, bcc):
    """Envia um email HTML"""
    gmail_manager = GmailManager()
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_body = f.read()
        
        gmail_manager.send_html_email(to, subject, html_body, cc, bcc)
    except Exception as e:
        print(f"Erro ao ler arquivo HTML: {e}")


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem para responder')
@click.option('--reply-text', required=True, help='Texto da resposta')
def reply(message_id, reply_text):
    """Responde a uma mensagem"""
    gmail_manager = GmailManager()
    gmail_manager.reply_to_message(message_id, reply_text)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem para encaminhar')
@click.option('--to', required=True, help='Destinatário')
@click.option('--forward-text', help='Texto adicional para o encaminhamento')
def forward(message_id, to, forward_text):
    """Encaminha uma mensagem"""
    gmail_manager = GmailManager()
    gmail_manager.forward_message(message_id, to, forward_text)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem para excluir')
def delete(message_id):
    """Exclui uma mensagem"""
    gmail_manager = GmailManager()
    gmail_manager.delete_message(message_id)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
def mark_read(message_id):
    """Marca mensagem como lida"""
    gmail_manager = GmailManager()
    gmail_manager.mark_as_read(message_id)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
def mark_unread(message_id):
    """Marca mensagem como não lida"""
    gmail_manager = GmailManager()
    gmail_manager.mark_as_unread(message_id)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
@click.option('--label-name', required=True, help='Nome do label')
def add_label(message_id, label_name):
    """Adiciona label a uma mensagem"""
    gmail_manager = GmailManager()
    gmail_manager.add_label(message_id, label_name)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
@click.option('--label-name', required=True, help='Nome do label')
def remove_label(message_id, label_name):
    """Remove label de uma mensagem"""
    gmail_manager = GmailManager()
    gmail_manager.remove_label(message_id, label_name)


@gmail.command()
@click.option('--query', help='Query de busca')
@click.option('--max-results', default=10, help='Número máximo de resultados')
def search(query, max_results):
    """Busca mensagens"""
    gmail_manager = GmailManager()
    messages = gmail_manager.search_messages(query, max_results)
    
    if messages:
        print(f"{'Assunto':<50} {'Remetente':<30} {'Data':<20} {'ID':<30}")
        print("-" * 130)
        for msg in messages:
            subject = msg['subject'][:49] if len(msg['subject']) > 49 else msg['subject']
            sender = msg['sender'][:29] if len(msg['sender']) > 29 else msg['sender']
            date = msg['date'][:19] if len(msg['date']) > 19 else msg['date']
            print(f"{subject:<50} {sender:<30} {date:<20} {msg['id']:<30}")
    else:
        print("Nenhuma mensagem encontrada.")


@gmail.command()
def unread_count():
    """Mostra contagem de mensagens não lidas"""
    gmail_manager = GmailManager()
    count = gmail_manager.get_unread_count()
    print(f"Mensagens não lidas: {count}")


@gmail.command()
def labels():
    """Lista todos os labels"""
    gmail_manager = GmailManager()
    labels = gmail_manager.get_labels()
    
    if labels:
        print("Labels disponíveis:")
        for label in labels:
            print(f"- {label['name']} (ID: {label['id']})")
    else:
        print("Nenhum label encontrado.")


@gmail.command()
@click.option('--name', required=True, help='Nome do novo label')
def create_label(name):
    """Cria um novo label"""
    gmail_manager = GmailManager()
    gmail_manager.create_label(name)


@gmail.command()
@click.option('--message-id', required=True, help='ID da mensagem')
@click.option('--attachment-id', required=True, help='ID do anexo')
@click.option('--filename', help='Nome do arquivo para salvar')
def download_attachment(message_id, attachment_id, filename):
    """Baixa um anexo"""
    gmail_manager = GmailManager()
    gmail_manager.download_attachment(message_id, attachment_id, filename)


if __name__ == '__main__':
    cli()
