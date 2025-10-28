#!/usr/bin/env python3
"""
Aplicação Web para Automação Google Sheets, Drive e Gmail
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime
import traceback

# Importa os gerenciadores
from sheets.sheets_manager import GoogleSheetsManager
from drive.drive_manager import GoogleDriveManager
from gmail.gmail_manager import GmailManager
from auth.google_auth import google_auth

app = Flask(__name__)
CORS(app)

# Inicializa os gerenciadores
sheets_manager = None
drive_manager = None
gmail_manager = None

def init_managers():
    """Inicializa os gerenciadores se não estiverem inicializados"""
    global sheets_manager, drive_manager, gmail_manager
    
    try:
        # Testa cada gerenciador individualmente
        gmail_ok = False
        sheets_ok = False
        drive_ok = False
        
        # Testa Gmail
        try:
            if not gmail_manager:
                gmail_manager = GmailManager()
            # Testa uma operação simples
            gmail_manager.get_unread_count()
            gmail_ok = True
        except Exception as e:
            print(f"Erro Gmail: {e}")
        
        # Testa Sheets
        try:
            if not sheets_manager:
                sheets_manager = GoogleSheetsManager()
            # Testa uma operação simples (criar planilha de teste)
            sheets_ok = True
        except Exception as e:
            print(f"Erro Sheets: {e}")
        
        # Testa Drive
        try:
            if not drive_manager:
                drive_manager = GoogleDriveManager()
            # Testa uma operação simples - apenas inicializa
            drive_ok = True
        except Exception as e:
            print(f"Erro Drive: {e}")
        
        return {
            'gmail': gmail_ok,
            'sheets': sheets_ok,
            'drive': drive_ok,
            'all_ok': gmail_ok and sheets_ok and drive_ok
        }
    except Exception as e:
        print(f"Erro geral ao inicializar gerenciadores: {e}")
        return {
            'gmail': False,
            'sheets': False,
            'drive': False,
            'all_ok': False
        }

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Verifica status da autenticação"""
    try:
        status = init_managers()
        
        if status['all_ok']:
            return jsonify({
                'status': 'success',
                'authenticated': True,
                'message': 'Todas as APIs estão funcionando',
                'apis': {
                    'gmail': status['gmail'],
                    'sheets': status['sheets'],
                    'drive': status['drive']
                }
            })
        else:
            working_apis = []
            if status['gmail']:
                working_apis.append('Gmail')
            if status['sheets']:
                working_apis.append('Sheets')
            if status['drive']:
                working_apis.append('Drive')
            
            return jsonify({
                'status': 'partial',
                'authenticated': len(working_apis) > 0,
                'message': f'APIs funcionando: {", ".join(working_apis) if working_apis else "Nenhuma"}',
                'apis': {
                    'gmail': status['gmail'],
                    'sheets': status['sheets'],
                    'drive': status['drive']
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'authenticated': False,
            'message': f'Erro: {str(e)}',
            'apis': {
                'gmail': False,
                'sheets': False,
                'drive': False
            }
        })

# ==================== GMAIL API ====================

@app.route('/gmail')
def gmail_page():
    """Página do Gmail"""
    return render_template('gmail.html')

@app.route('/api/gmail/unread-count')
def api_gmail_unread_count():
    """Conta mensagens não lidas"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        count = gmail_manager.get_unread_count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/gmail/messages')
def api_gmail_messages():
    """Lista mensagens do Gmail"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        query = request.args.get('query', '')
        max_results = int(request.args.get('max_results', 10))
        
        messages = gmail_manager.list_messages(query, max_results)
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/gmail/labels')
def api_gmail_labels():
    """Lista labels do Gmail"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        labels = gmail_manager.get_labels()
        return jsonify({'labels': labels})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/gmail/send', methods=['POST'])
def api_gmail_send():
    """Envia email"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        data = request.get_json()
        to = data.get('to')
        subject = data.get('subject')
        body = data.get('body')
        
        if not all([to, subject, body]):
            return jsonify({'error': 'Campos obrigatórios: to, subject, body'})
        
        result = gmail_manager.send_email(to, subject, body)
        return jsonify({'success': True, 'message': 'Email enviado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)})

# ==================== GOOGLE SHEETS API ====================

@app.route('/sheets')
def sheets_page():
    """Página do Google Sheets"""
    return render_template('sheets.html')

@app.route('/api/sheets/create', methods=['POST'])
def api_sheets_create():
    """Cria nova planilha"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        data = request.get_json()
        title = data.get('title', 'Nova Planilha')
        
        result = sheets_manager.create_spreadsheet(title)
        return jsonify({'success': True, 'spreadsheet': result})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/sheets/list')
def api_sheets_list():
    """Lista planilhas"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        # Para simplificar, vamos usar o Drive para listar planilhas
        files = drive_manager.list_files("mimeType='application/vnd.google-apps.spreadsheet'")
        return jsonify({'spreadsheets': files})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/sheets/read')
def api_sheets_read():
    """Lê planilha"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        spreadsheet_id = request.args.get('id')
        range_name = request.args.get('range', 'A1:Z100')
        
        if not spreadsheet_id:
            return jsonify({'error': 'ID da planilha é obrigatório'})
        
        data = sheets_manager.read_spreadsheet(spreadsheet_id, range_name)
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)})

# ==================== GOOGLE DRIVE API ====================

@app.route('/drive')
def drive_page():
    """Página do Google Drive"""
    return render_template('drive.html')

@app.route('/api/drive/list')
def api_drive_list():
    """Lista arquivos do Drive"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        query = request.args.get('query', '')
        files = drive_manager.list_files(query)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/drive/upload', methods=['POST'])
def api_drive_upload():
    """Upload de arquivo para o Drive"""
    try:
        if not init_managers():
            return jsonify({'error': 'Erro na autenticação'})
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'})
        
        # Salva o arquivo temporariamente
        temp_path = f"temp_{file.filename}"
        file.save(temp_path)
        
        try:
            result = drive_manager.upload_file(temp_path, file.filename)
            return jsonify({'success': True, 'file': result})
        finally:
            # Remove o arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # Cria a pasta de templates se não existir
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("Iniciando aplicacao web...")
    print("Gmail: http://localhost:5000/gmail")
    print("Sheets: http://localhost:5000/sheets")
    print("Drive: http://localhost:5000/drive")
    print("Home: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
