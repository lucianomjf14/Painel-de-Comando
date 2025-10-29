#!/usr/bin/env python3
"""
Aplicação Web para Automação Google Sheets, Drive e Gmail
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS, cross_origin
import json
import os
from datetime import datetime
import traceback
from threading import Lock

# Importa os gerenciadores
from sheets.sheets_manager import GoogleSheetsManager
from drive.drive_manager import GoogleDriveManager
from gmail.gmail_manager import GmailManager
from auth.google_auth import google_auth

app = Flask(__name__)
CORS(app)


@app.context_processor
def inject_template_defaults():
    return {
        'breadcrumbs': [],
        'show_user_header': False
    }

# Adiciona headers para prevenir cache
@app.after_request
def add_no_cache_headers(response):
    """Adiciona headers para prevenir cache de respostas da API"""
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Inicializa os gerenciadores - Singleton pattern com controle de concorrência
sheets_manager: GoogleSheetsManager = None
drive_manager: GoogleDriveManager = None
gmail_manager: GmailManager = None
_init_lock = Lock()
_setup_done = False
_setup_lock = Lock()

# ==================== Respostas e Erros Padronizados ====================

def api_success(data, status_code=200):
    """Gera uma resposta de sucesso padronizada para a API."""
    return jsonify({'status': 'success', 'data': data}), status_code

def api_error(message, status_code=400):
    """Gera uma resposta de erro padronizada para a API."""
    response = jsonify({'status': 'error', 'message': message})
    response.status_code = status_code
    return response

@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Captura exceções genéricas e retorna um erro 500."""
    print(f"Erro não tratado: {e}")
    traceback.print_exc()
    return api_error("Ocorreu um erro interno no servidor.", 500)


def _build_status(gmail_ok: bool, sheets_ok: bool, drive_ok: bool) -> dict:
    """Retorna o status consolidado das APIs."""
    return {
        'gmail': gmail_ok,
        'sheets': sheets_ok,
        'drive': drive_ok,
        'all_ok': gmail_ok and sheets_ok and drive_ok
    }


def build_breadcrumbs(*segments):
    """Retorna breadcrumbs padrão a partir de segmentos (label, endpoint/None)."""
    if not segments:
        return []

    crumbs = [{'label': 'Início', 'url': url_for('index')}]

    for idx, segment in enumerate(segments):
        params = {}
        if isinstance(segment, dict):
            label = segment.get('label')
            endpoint = segment.get('endpoint')
            params = segment.get('params', {})
        else:
            try:
                label, endpoint = segment
            except (TypeError, ValueError):
                raise ValueError("Segmentos de breadcrumb devem ser tuplas (label, endpoint) ou dicts com 'label'.")

        if not label:
            raise ValueError("Segmento de breadcrumb requer 'label'.")

        is_last = idx == len(segments) - 1
        url_value = None
        if endpoint and not is_last:
            url_value = url_for(endpoint, **params)

        crumbs.append({'label': label, 'url': url_value})

    return crumbs


def init_managers():
    """Inicializa os gerenciadores se não estiverem prontos."""
    global sheets_manager, drive_manager, gmail_manager

    with _init_lock:
        gmail_ok = isinstance(gmail_manager, GmailManager)
        sheets_ok = sheets_manager is not None
        drive_ok = drive_manager is not None

        try:
            if not gmail_ok:
                gmail_manager = GmailManager()
                gmail_ok = True
        except Exception as e:
            gmail_ok = False
            print(f"Erro Gmail: {e}")

        try:
            if not sheets_ok:
                sheets_manager = GoogleSheetsManager()
                sheets_ok = True
        except Exception as e:
            sheets_ok = False
            print(f"Erro Sheets: {e}")

        try:
            if not drive_ok:
                drive_manager = GoogleDriveManager()
                drive_ok = True
        except Exception as e:
            drive_ok = False
            print(f"Erro Drive: {e}")

        return _build_status(gmail_ok, sheets_ok, drive_ok)


def ensure_setup():
    """Garante que autenticação e gerenciadores sejam configurados uma única vez."""
    global _setup_done

    if _setup_done:
        return

    with _setup_lock:
        if _setup_done:
            return

        print("=" * 60)
        print("Executando setup inicial antes da primeira requisição...")
        print("=" * 60)
        try:
            google_auth.authenticate()
            status = init_managers()

            if google_auth.credentials and google_auth.credentials.valid and status['all_ok']:
                print("Setup inicial concluído: autenticação e gerenciadores OK.")
            else:
                print("Aviso: setup inicial incompleto. Verifique autenticação e APIs.")
                print(f"Status: {status}")

        except Exception as e:
            print(f"Erro crítico no setup inicial: {e}")
            traceback.print_exc()
        finally:
            _setup_done = True
            print("=" * 60)


@app.before_request
def before_request_setup():
    """Garante que o setup seja executado antes de cada requisição."""
    ensure_setup()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html', breadcrumbs=[], show_user_header=False)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon or returns 204 if not found"""
    from flask import send_from_directory
    import os
    favicon_path = os.path.join(app.root_path, 'static')
    if os.path.exists(os.path.join(favicon_path, 'favicon.ico')):
        return send_from_directory(favicon_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    return '', 204  # No Content

@app.route('/settings')
def settings_page():
    """Página de configurações gerais"""
    crumbs = build_breadcrumbs(('Configurações', None))
    return render_template('settings.html', breadcrumbs=crumbs, show_user_header=True)

@app.route('/logos/<path:filename>')
def serve_logo(filename):
    """Serve arquivos de logo armazenados na pasta /logos"""
    from flask import send_from_directory, abort
    logo_dir = os.path.join(app.root_path, 'logos')
    file_path = os.path.join(logo_dir, filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(logo_dir, filename)

@app.route('/api/user-profile')
def api_user_profile():
    """Retorna informações do perfil do usuário"""
    try:
        # Verifica autenticação
        if not (google_auth.credentials and google_auth.credentials.valid):
            return jsonify({
                'error': 'Não autenticado',
                'message': 'A autenticação falhou ou ainda não foi concluída.'
            }), 401
        
        if not gmail_manager:
            return jsonify({
                'error': 'Gmail não disponível',
                'message': 'O serviço do Gmail não está disponível.'
            }), 503
        
        # 1. Busca informações do OAuth2 (com retries internos)
        user_info = google_auth.get_oauth_user_info()
        if not user_info:
            return jsonify({
                'error': 'Falha OAuth2',
                'message': 'Falha ao obter informações do perfil OAuth2.'
            }), 500

        # 2. Busca perfil do Gmail (com retries internos)
        gmail_profile = gmail_manager.get_user_profile()
        if not gmail_profile:
            return jsonify({
                'error': 'Falha Gmail',
                'message': 'Falha ao obter perfil do Gmail.'
            }), 500
        
        # Combina os resultados
        profile_data = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name'),
            'picture': user_info.get('picture'),
            'locale': user_info.get('locale'),
            'verified_email': user_info.get('verified_email'),
            'messagesTotal': gmail_profile.get('messagesTotal', 0),
            'threadsTotal': gmail_profile.get('threadsTotal', 0),
            'historyId': gmail_profile.get('historyId')
        }
        
        # Retorna diretamente sem o wrapper 'data' para compatibilidade com frontend
        return jsonify(profile_data)
        
    except Exception as e:
        print(f"Erro ao obter perfil: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'message': f'Erro ao obter informações do perfil: {str(e)}'
        }), 500

@app.route('/api/status')
def api_status():
    """Verifica status da autenticação"""
    try:
        # A verificação agora é feita pelo before_first_request
        if not (google_auth.credentials and google_auth.credentials.valid):
            return jsonify({
                'status': 'error',
                'authenticated': False,
                'message': 'Não autenticado. A autenticação falhou ou não foi concluída.',
                'apis': {'gmail': False, 'sheets': False, 'drive': False}
            }), 401
        
        # O status dos gerenciadores já foi definido na inicialização
        status = init_managers()
        
        if status['all_ok']:
            return jsonify({
                'status': 'success',
                'authenticated': True,
                'message': 'Todas as APIs estão funcionando',
                'apis': status
            })
        else:
            working_apis = [k for k, v in status.items() if v and k != 'all_ok']
            return jsonify({
                'status': 'partial',
                'authenticated': len(working_apis) > 0,
                'message': f'APIs funcionando: {", ".join(working_apis) if working_apis else "Nenhuma"}',
                'apis': status
            })
    except Exception as e:
        print(f"Erro ao verificar status: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'authenticated': False,
            'message': f'Erro: {str(e)}',
            'apis': {'gmail': False, 'sheets': False, 'drive': False}
        }), 500

# ==================== GMAIL API ====================

@app.route('/gmail')
def gmail_page():
    """Página do Gmail"""
    crumbs = build_breadcrumbs(('Gmail', None))
    return render_template('gmail.html', breadcrumbs=crumbs, show_user_header=True)

@app.route('/api/gmail/unread-count')
def api_gmail_unread_count():
    """Conta mensagens não lidas"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        count = gmail_manager.get_unread_count()
        return api_success({'count': count})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/messages')
def api_gmail_messages():
    """Lista mensagens do Gmail"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        query = request.args.get('query', '')
        max_results = int(request.args.get('max_results', 10))
        page_token = request.args.get('page_token') or None
        result = gmail_manager.list_messages(query, max_results, page_token)
        return api_success(result)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/labels')
def api_gmail_labels():
    """Lista labels do Gmail"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        labels = gmail_manager.get_labels()
        return api_success({'labels': labels})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/send', methods=['POST'])
def api_gmail_send():
    """Envia email"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        data = request.get_json()
        to = data.get('to')
        subject = data.get('subject')
        body = data.get('body')

        if not all([to, subject, body]):
            return api_error('Campos obrigatórios: to, subject, body', 400)

        result = gmail_manager.send_email(to, subject, body)
        if result:
            return api_success({'sent': True, 'message': 'Email enviado com sucesso'}, 201)
        else:
            return api_error('Falha ao enviar email', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/message/<message_id>')
def api_gmail_get_message(message_id):
    """Obtém detalhes de uma mensagem específica"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        message = gmail_manager.get_message(message_id)
        if message:
            return api_success({'message': message})
        else:
            return api_error('Mensagem não encontrada', 404)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/message/<message_id>/mark-read', methods=['POST'])
def api_gmail_mark_read(message_id):
    """Marca mensagem como lida"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        result = gmail_manager.mark_messages_read([message_id])
        if result:
            return api_success({'marked': True, 'message': 'Mensagem marcada como lida'})
        else:
            return api_error('Falha ao marcar como lida', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/message/<message_id>/mark-unread', methods=['POST'])
def api_gmail_mark_unread(message_id):
    """Marca mensagem como não lida"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        result = gmail_manager.mark_messages_unread([message_id])
        if result:
            return api_success({'marked': True, 'message': 'Mensagem marcada como não lida'})
        else:
            return api_error('Falha ao marcar como não lida', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/message/<message_id>/archive', methods=['POST'])
def api_gmail_archive(message_id):
    """Arquiva mensagem (remove da inbox)"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        # Arquivar = remover label INBOX
        result = gmail_manager.archive_messages([message_id])
        if result:
            return api_success({'archived': True, 'message': 'Mensagem arquivada'})
        else:
            return api_error('Falha ao arquivar', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/messages/batch', methods=['POST'])
def api_gmail_messages_batch():
    """Executa ações em lote em mensagens do Gmail"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        data = request.get_json() or {}
        action = data.get('action')
        ids = data.get('ids') or []

        if not ids or not isinstance(ids, list):
            return api_error('Nenhuma mensagem selecionada.', 400)

        action_map = {
            'archive': (gmail_manager.archive_messages, 'Mensagens arquivadas'),
            'mark_read': (gmail_manager.mark_messages_read, 'Mensagens marcadas como lidas'),
            'mark_unread': (gmail_manager.mark_messages_unread, 'Mensagens marcadas como não lidas'),
            'delete': (gmail_manager.delete_messages, 'Mensagens excluídas')
        }

        if action not in action_map:
            return api_error('Ação inválida.', 400)

        handler, success_message = action_map[action]
        result = handler(ids)

        if result:
            return api_success({'processed': ids, 'action': action, 'message': success_message})
        return api_error('Falha ao executar ação em lote.', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/gmail/message/<message_id>/reply', methods=['POST'])
def api_gmail_reply(message_id):
    """Responde a uma mensagem"""
    try:
        if not gmail_manager: return api_error('Serviço do Gmail não disponível.', 503)
        data = request.get_json()
        reply_text = data.get('reply_text')

        if not reply_text:
            return api_error('Campo obrigatório: reply_text', 400)

        result = gmail_manager.reply_to_message(message_id, reply_text)
        if result:
            return api_success({'sent': True, 'message': 'Resposta enviada com sucesso'})
        else:
            return api_error('Falha ao enviar resposta', 500)
    except Exception as e:
        return api_error(str(e))

# ==================== GOOGLE SHEETS API ====================

@app.route('/sheets')
def sheets_page():
    """Página do Google Sheets"""
    crumbs = build_breadcrumbs(('Google Sheets', None))
    return render_template('sheets.html', breadcrumbs=crumbs, show_user_header=True)

@app.route('/api/sheets/create', methods=['POST'])
def api_sheets_create():
    """Cria nova planilha"""
    try:
        if not sheets_manager: return api_error('Serviço do Sheets não disponível.', 503)
        data = request.get_json()
        title = data.get('title', 'Nova Planilha')
        result = sheets_manager.create_spreadsheet(title)
        return api_success({'spreadsheet': result}, 201)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/sheets/list')
def api_sheets_list():
    """Lista planilhas"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível para listar planilhas.', 503)
        # Para simplificar, vamos usar o Drive para listar planilhas
        files = drive_manager.list_files("mimeType='application/vnd.google-apps.spreadsheet'")
        return api_success({'spreadsheets': files})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/sheets/read')
def api_sheets_read():
    """Lê planilha"""
    try:
        if not sheets_manager: return api_error('Serviço do Sheets não disponível.', 503)
        spreadsheet_id = request.args.get('id')
        range_name = request.args.get('range', 'A1:Z100')
        
        if not spreadsheet_id:
            return api_error('O parâmetro "id" da planilha é obrigatório.', 400)
        
        data = sheets_manager.read_spreadsheet(spreadsheet_id, range_name)
        return api_success({'data': data})
    except Exception as e:
        return api_error(str(e))

# ==================== GOOGLE DRIVE API ====================

@app.route('/drive')
def drive_page():
    """Página do Google Drive"""
    crumbs = build_breadcrumbs(('Google Drive', None))
    return render_template('drive.html', breadcrumbs=crumbs, show_user_header=True)

@app.route('/status')
def status_page():
    """Mantém compatibilidade redirecionando para configurações"""
    return redirect(url_for('settings_page'))

@app.route('/api/drive/list')
def api_drive_list():
    """Lista arquivos do Drive"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        query = request.args.get('query', '')
        files = drive_manager.list_files(query)
        return api_success({'files': files})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/upload', methods=['POST'])
def api_drive_upload():
    """Upload de arquivo para o Drive"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        
        if 'file' not in request.files:
            return api_error('Nenhum arquivo enviado na requisição.', 400)
        
        file = request.files['file']
        if file.filename == '':
            return api_error('Nenhum arquivo selecionado para upload.', 400)
        
        # Upload do arquivo em memória, sem salvar em disco
        # Nota: drive_manager.upload_file precisará ser ajustado para aceitar um stream
        # Se o seu drive_manager.upload_file espera um caminho de arquivo, a abordagem original é necessária,
        # mas esta é a ideal. Assumindo que upload_file pode ser adaptado:
        result = drive_manager.upload_file_from_stream(file.filename, file.stream, file.mimetype)
        return api_success({'file': result}, 201)
    except Exception as e:
        return api_error(str(e))

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
