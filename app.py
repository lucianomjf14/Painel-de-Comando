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
from ai.document_analyzer import document_analyzer
from ai.analysis_queue import analysis_queue
from ai.background_worker import document_worker, scan_progress

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
                
                # Inicia worker de análise automaticamente
                if drive_manager and not document_worker.running:
                    print("🤖 Iniciando worker de análise automática...")
                    document_worker.set_drive_manager(drive_manager)
                    
                    # Configura auto-scan para o Drive EMPRESAS
                    drive_id = '0AMPhv1qxMn1fUk9PVA'
                    employees_folder_id = '1-gxsARkjRPoK8VSzUeUe0zb_5BDgGkCN'  # ID correto - 1. RH
                    document_worker.configure_auto_scan(drive_id, employees_folder_id)
                    
                    # Inicia o worker com auto-scan ativo
                    document_worker.start()
                    print(f"✅ Worker ativo com auto-scan (intervalo: {document_worker.scan_interval}s)")
                
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
        spreadsheet_id = sheets_manager.create_spreadsheet(title)
        
        if spreadsheet_id:
            result = {
                'id': spreadsheet_id,
                'title': title,
                'url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
            }
            return api_success({'spreadsheet': result}, 201)
        else:
            return api_error('Falha ao criar planilha', 500)
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
        if not sheets_manager: 
            return api_error('Serviço do Sheets não disponível.', 503)
        
        spreadsheet_id = request.args.get('id')
        range_name = request.args.get('range', 'A1:Z1000')  # Aumentado para Z1000
        
        if not spreadsheet_id:
            return api_error('O parâmetro "id" da planilha é obrigatório.', 400)
        
        print(f"\n{'='*60}")
        print(f"Lendo planilha: {spreadsheet_id}")
        print(f"Range solicitado: {range_name}")
        print(f"{'='*60}")
        
        df = sheets_manager.read_spreadsheet(spreadsheet_id, range_name)
        
        print(f"DataFrame retornado:")
        print(f"  - Vazio: {df.empty}")
        print(f"  - Linhas: {len(df)}")
        print(f"  - Colunas: {len(df.columns) if not df.empty else 0}")
        
        # Converte DataFrame para lista de listas (formato JSON serializável)
        if df.empty:
            print("⚠️  Planilha vazia, retornando array vazio")
            data = []
        else:
            # Inclui o cabeçalho como primeira linha
            data = [df.columns.tolist()] + df.values.tolist()
            print(f"✅ Dados convertidos: {len(data)} linhas (incluindo cabeçalho)")
        
        return api_success({'data': data})
        
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")
        import traceback
        traceback.print_exc()
        return api_error(f'Erro ao ler planilha: {str(e)}')

@app.route('/api/sheets/<sheet_id>/rename', methods=['POST'])
def api_sheets_rename(sheet_id):
    """Renomeia uma planilha"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return api_error('O parâmetro "name" é obrigatório.', 400)
        
        result = drive_manager.rename_file(sheet_id, new_name)
        if result:
            return api_success({'message': 'Planilha renomeada com sucesso', 'name': new_name})
        else:
            return api_error('Falha ao renomear planilha', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/sheets/<sheet_id>/delete', methods=['DELETE'])
def api_sheets_delete(sheet_id):
    """Exclui uma planilha"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        
        permanent = request.args.get('permanent', 'false').lower() == 'true'
        result = drive_manager.delete_file(sheet_id, permanent)
        
        if result:
            msg = 'Planilha excluída permanentemente' if permanent else 'Planilha movida para lixeira'
            return api_success({'message': msg})
        else:
            return api_error('Falha ao excluir planilha', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/sheets/<sheet_id>/export')
def api_sheets_export(sheet_id):
    """Exporta planilha para CSV"""
    try:
        if not sheets_manager: return api_error('Serviço do Sheets não disponível.', 503)
        
        range_name = request.args.get('range', 'A1:Z1000')
        csv_content = sheets_manager.export_to_csv(sheet_id, range_name)
        
        if csv_content:
            from flask import Response
            # Obtém o nome da planilha
            file_info = drive_manager.get_file_info(sheet_id) if drive_manager else {}
            filename = file_info.get('name', 'planilha') + '.csv'
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        else:
            return api_error('Falha ao exportar planilha', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/sheets/<sheet_id>/update', methods=['POST'])
def api_sheets_update(sheet_id):
    """Atualiza dados da planilha"""
    try:
        if not sheets_manager: return api_error('Serviço do Sheets não disponível.', 503)
        
        data = request.get_json()
        range_name = data.get('range')
        values = data.get('values')
        
        if not range_name or not values:
            return api_error('Parâmetros "range" e "values" são obrigatórios.', 400)
        
        result = sheets_manager.write_to_spreadsheet(sheet_id, range_name, values)
        
        if result:
            return api_success({'message': 'Planilha atualizada com sucesso'})
        else:
            return api_error('Falha ao atualizar planilha', 500)
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

@app.route('/api/drive/shared')
def api_drive_shared():
    """Lista arquivos compartilhados comigo"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        files = drive_manager.list_shared_with_me()
        return api_success({'files': files})
    except Exception as e:
        return api_error(str(e))

# ===== ENDPOINTS DE DRIVES COMPARTILHADOS (TEMPO REAL) =====

@app.route('/api/drive/shared-drives')
def api_drive_shared_drives():
    """Lista todos os drives compartilhados do usuário"""
    try:
        if not drive_manager: 
            return api_error('Serviço do Drive não disponível.', 503)
        drives = drive_manager.list_shared_drives()
        return api_success({'drives': drives})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/shared-drives/<drive_id>/folder')
@app.route('/api/drive/shared-drives/<drive_id>/folder/<folder_id>')
def api_drive_folder_contents(drive_id, folder_id=None):
    """
    Lista conteúdo de uma pasta em tempo real
    Se folder_id não for fornecido, lista a raiz do drive
    """
    try:
        if not drive_manager: 
            return api_error('Serviço do Drive não disponível.', 503)
        
        contents = drive_manager.list_files_in_shared_drive(drive_id, parent_id=folder_id)
        return api_success({'contents': contents})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/shared-drives/<drive_id>/stats')
@app.route('/api/drive/shared-drives/<drive_id>/stats/<folder_id>')
def api_drive_folder_stats(drive_id, folder_id=None):
    """Retorna estatísticas de um drive ou pasta específica"""
    try:
        if not drive_manager: 
            return api_error('Serviço do Drive não disponível.', 503)
        
        stats = drive_manager.get_folder_stats(drive_id, folder_id)
        return api_success({'stats': stats})
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/shared-drives/<drive_id>/search')
def api_drive_search(drive_id):
    """Busca arquivos em um drive compartilhado"""
    try:
        if not drive_manager: 
            return api_error('Serviço do Drive não disponível.', 503)
        
        query = request.args.get('q', '')
        if not query:
            return api_error('Parâmetro de busca "q" é obrigatório', 400)
        
        results = drive_manager.search_in_drive(drive_id, query)
        return api_success({'items': results})
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
        
        # Salva temporariamente e faz upload
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file.save(tmp.name)
            result = drive_manager.upload_file(tmp.name, name=file.filename)
            os.unlink(tmp.name)
        
        if result:
            return api_success({'file': {'id': result, 'name': file.filename}}, 201)
        else:
            return api_error('Falha ao fazer upload', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/<file_id>/rename', methods=['POST'])
def api_drive_rename(file_id):
    """Renomeia um arquivo do Drive"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return api_error('O parâmetro "name" é obrigatório.', 400)
        
        result = drive_manager.rename_file(file_id, new_name)
        if result:
            return api_success({'message': 'Arquivo renomeado com sucesso', 'name': new_name})
        else:
            return api_error('Falha ao renomear arquivo', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/<file_id>/delete', methods=['DELETE'])
def api_drive_delete(file_id):
    """Exclui um arquivo do Drive"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        
        permanent = request.args.get('permanent', 'false').lower() == 'true'
        result = drive_manager.delete_file(file_id, permanent)
        
        if result:
            msg = 'Arquivo excluído permanentemente' if permanent else 'Arquivo movido para lixeira'
            return api_success({'message': msg})
        else:
            return api_error('Falha ao excluir arquivo', 500)
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/<file_id>/download')
def api_drive_download(file_id):
    """Faz download de um arquivo do Drive"""
    try:
        if not drive_manager: return api_error('Serviço do Drive não disponível.', 503)
        
        import tempfile
        import io
        from flask import send_file
        
        # Obtém informações do arquivo
        file_info = drive_manager.get_file_info(file_id)
        filename = file_info.get('name', 'download')
        
        # Faz download para memória
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            result = drive_manager.download_file(file_id, tmp.name)
            
            if result:
                return send_file(
                    tmp.name,
                    as_attachment=True,
                    download_name=filename
                )
            else:
                os.unlink(tmp.name)
                return api_error('Falha ao fazer download', 500)
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

# ============================================================================
# ROTAS PARA GERENCIAMENTO DE ESTRUTURA DE FUNCIONÁRIOS
# ============================================================================

@app.route('/api/drive/employee/create-structure', methods=['POST'])
def api_create_employee_structure():
    """Cria a estrutura padrão de 12 pastas para um funcionário"""
    try:
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        data = request.get_json()
        employee_folder_id = data.get('employee_folder_id')
        drive_id = data.get('drive_id')
        
        if not employee_folder_id:
            return api_error('ID da pasta do funcionário é obrigatório', 400)
        
        result = drive_manager.create_employee_folder_structure(employee_folder_id, drive_id)
        
        if result['success']:
            return api_success(result)
        else:
            return api_error(result.get('errors', ['Erro desconhecido']), 500)
            
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/employee/validate-structure', methods=['POST'])
def api_validate_employee_structure():
    """Valida a estrutura de pastas de um funcionário"""
    try:
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        data = request.get_json()
        employee_folder_id = data.get('employee_folder_id')
        drive_id = data.get('drive_id')
        
        if not employee_folder_id:
            return api_error('ID da pasta do funcionário é obrigatório', 400)
        
        result = drive_manager.validate_employee_structure(employee_folder_id, drive_id)
        return api_success(result)
            
    except Exception as e:
        return api_error(str(e))

@app.route('/api/drive/employee/complete-structure', methods=['POST'])
def api_complete_employee_structure():
    """Valida e completa a estrutura de pastas de um funcionário"""
    try:
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        data = request.get_json()
        employee_folder_id = data.get('employee_folder_id')
        drive_id = data.get('drive_id')
        
        if not employee_folder_id:
            return api_error('ID da pasta do funcionário é obrigatório', 400)
        
        result = drive_manager.complete_employee_structure(employee_folder_id, drive_id)
        
        if result['success']:
            return api_success(result)
        else:
            return api_error(result.get('message', 'Erro ao completar estrutura'), 500)
            
    except Exception as e:
        return api_error(str(e))

# ============================================================================
# ROTAS PARA ANÁLISE INTELIGENTE DE DOCUMENTOS COM IA
# ============================================================================

@app.route('/api/drive/employee/analyze-documents', methods=['POST'])
def api_analyze_employee_documents():
    """Analisa todos os documentos de um funcionário e sugere padronização"""
    try:
        data = request.get_json()
        employee_folder_id = data.get('employee_folder_id')
        employee_code = data.get('employee_code')
        employee_name = data.get('employee_name')
        drive_id = data.get('drive_id')
        
        if not all([employee_folder_id, employee_code, employee_name]):
            return api_error('Parâmetros obrigatórios faltando', 400)
        
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        # Lista todas as subpastas do funcionário
        contents = drive_manager.list_files_in_shared_drive(drive_id, parent_id=employee_folder_id)
        subpastas = contents.get('folders', [])
        
        total_analysis = {
            'employee_code': employee_code,
            'employee_name': employee_name,
            'total_files_analyzed': 0,
            'total_to_rename': 0,
            'total_ok': 0,
            'by_folder': {},
            'all_suggestions': []
        }
        
        # Analisa cada subpasta
        for pasta in subpastas:
            folder_name = pasta['name']
            folder_id = pasta['id']
            
            # Lista arquivos da pasta
            folder_contents = drive_manager.list_files_in_shared_drive(drive_id, parent_id=folder_id)
            files = folder_contents.get('files', [])
            
            # Analisa documentos
            suggestions = document_analyzer.analyze_folder_documents(
                files,
                folder_name,
                employee_code,
                employee_name
            )
            
            # Conta estatísticas
            to_rename = sum(1 for s in suggestions if s['action'] == 'rename')
            ok = sum(1 for s in suggestions if s['action'] == 'keep')
            
            total_analysis['total_files_analyzed'] += len(suggestions)
            total_analysis['total_to_rename'] += to_rename
            total_analysis['total_ok'] += ok
            
            total_analysis['by_folder'][folder_name] = {
                'total': len(suggestions),
                'to_rename': to_rename,
                'ok': ok,
                'suggestions': suggestions
            }
            
            total_analysis['all_suggestions'].extend(suggestions)
        
        return api_success(total_analysis)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/drive/employee/rename-documents', methods=['POST'])
def api_rename_employee_documents():
    """Renomeia documentos de um funcionário baseado nas sugestões da IA"""
    try:
        data = request.get_json()
        suggestions = data.get('suggestions', [])
        drive_id = data.get('drive_id')
        
        if not suggestions:
            return api_error('Nenhuma sugestão fornecida', 400)
        
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        results = {
            'total': len(suggestions),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for suggestion in suggestions:
            file_id = suggestion.get('file_id')
            new_name = suggestion.get('suggested_name')
            original_name = suggestion.get('original_name')
            
            if not file_id or not new_name:
                continue
            
            try:
                # Renomeia o arquivo
                success = drive_manager.rename_file(file_id, new_name)
                
                if success:
                    results['success'] += 1
                    results['details'].append({
                        'file_id': file_id,
                        'original': original_name,
                        'new': new_name,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'file_id': file_id,
                        'original': original_name,
                        'new': new_name,
                        'status': 'failed'
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'file_id': file_id,
                    'original': original_name,
                    'error': str(e),
                    'status': 'error'
                })
        
        return api_success(results)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

# ============================================================================
# ROTAS - NOTIFICAÇÕES DE ANÁLISE DE DOCUMENTOS
# ============================================================================

@app.route('/api/notifications/pending', methods=['GET'])
def api_get_pending_notifications():
    """Retorna o contador e lista de notificações pendentes"""
    try:
        # Busca sugestões pendentes
        pending = analysis_queue.get_pending_suggestions()
        
        # Agrupa por funcionário
        by_employee = {}
        for suggestion in pending:
            employee_name = suggestion.get('employee_name', 'Desconhecido')
            if employee_name not in by_employee:
                by_employee[employee_name] = {
                    'employee_name': employee_name,
                    'employee_code': suggestion.get('employee_code'),
                    'count': 0,
                    'suggestions': []
                }
            
            by_employee[employee_name]['count'] += 1
            by_employee[employee_name]['suggestions'].append(suggestion)
        
        result = {
            'total_count': len(pending),
            'total_employees': len(by_employee),
            'by_employee': list(by_employee.values()),
            'suggestions': pending
        }
        
        return api_success(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/notifications/approve', methods=['POST'])
def api_approve_suggestion():
    """Aprova uma sugestão e renomeia o arquivo"""
    try:
        data = request.get_json()
        suggestion_id = data.get('suggestion_id')
        
        if not suggestion_id:
            return api_error('ID da sugestão não fornecido', 400)
        
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        # Busca a sugestão
        suggestion = analysis_queue.get_suggestion(suggestion_id)
        
        if not suggestion:
            return api_error('Sugestão não encontrada', 404)
        
        # Renomeia o arquivo
        try:
            success = drive_manager.rename_file(
                suggestion['file_id'], 
                suggestion['suggested_name']
            )
            
            if success:
                # Marca como aplicado
                analysis_queue.update_suggestion_status(suggestion_id, 'applied')
                
                return api_success({
                    'suggestion_id': suggestion_id,
                    'status': 'applied',
                    'original_name': suggestion['original_name'],
                    'new_name': suggestion['suggested_name']
                })
            else:
                # Marca como falha
                analysis_queue.update_suggestion_status(suggestion_id, 'failed')
                return api_error('Falha ao renomear arquivo', 500)
                
        except Exception as e:
            # Marca como falha
            analysis_queue.update_suggestion_status(suggestion_id, 'failed')
            return api_error(f'Erro ao renomear: {str(e)}', 500)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/notifications/reject', methods=['POST'])
def api_reject_suggestion():
    """Rejeita uma sugestão"""
    try:
        data = request.get_json()
        suggestion_id = data.get('suggestion_id')
        
        if not suggestion_id:
            return api_error('ID da sugestão não fornecido', 400)
        
        # Marca como rejeitado
        analysis_queue.update_suggestion_status(suggestion_id, 'rejected')
        
        return api_success({
            'suggestion_id': suggestion_id,
            'status': 'rejected'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/notifications/approve-batch', methods=['POST'])
def api_approve_batch():
    """Aprova múltiplas sugestões de uma vez"""
    try:
        data = request.get_json()
        suggestion_ids = data.get('suggestion_ids', [])
        
        if not suggestion_ids:
            return api_error('Nenhuma sugestão fornecida', 400)
        
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        results = {
            'total': len(suggestion_ids),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for suggestion_id in suggestion_ids:
            suggestion = analysis_queue.get_suggestion(suggestion_id)
            
            if not suggestion:
                results['failed'] += 1
                results['details'].append({
                    'suggestion_id': suggestion_id,
                    'status': 'not_found'
                })
                continue
            
            try:
                success = drive_manager.rename_file(
                    suggestion['file_id'], 
                    suggestion['suggested_name']
                )
                
                if success:
                    analysis_queue.update_suggestion_status(suggestion_id, 'applied')
                    results['success'] += 1
                    results['details'].append({
                        'suggestion_id': suggestion_id,
                        'status': 'applied',
                        'original_name': suggestion['original_name'],
                        'new_name': suggestion['suggested_name']
                    })
                else:
                    analysis_queue.update_suggestion_status(suggestion_id, 'failed')
                    results['failed'] += 1
                    results['details'].append({
                        'suggestion_id': suggestion_id,
                        'status': 'failed'
                    })
                    
            except Exception as e:
                analysis_queue.update_suggestion_status(suggestion_id, 'failed')
                results['failed'] += 1
                results['details'].append({
                    'suggestion_id': suggestion_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return api_success(results)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/notifications/scan-all', methods=['POST'])
def api_scan_all_documents():
    """Escaneia todos os documentos dos funcionários e adiciona à fila de análise"""
    try:
        data = request.get_json()
        drive_id = data.get('drive_id')
        employees_folder_id = data.get('employees_folder_id')
        
        if not drive_id or not employees_folder_id:
            return api_error('drive_id e employees_folder_id são obrigatórios', 400)
        
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        # Configura o drive manager no worker
        document_worker.set_drive_manager(drive_manager)
        
        # Inicia o scanner em uma thread separada para não bloquear a resposta
        def run_scanner():
            document_worker.scan_employee_folders(drive_id, employees_folder_id)
        
        import threading
        scanner_thread = threading.Thread(target=run_scanner, daemon=True)
        scanner_thread.start()
        
        return api_success({
            'message': 'Scanner iniciado em background',
            'drive_id': drive_id,
            'employees_folder_id': employees_folder_id
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/worker/start', methods=['POST'])
def api_start_worker():
    """Inicia o worker de análise de documentos"""
    try:
        if not drive_manager:
            return api_error('Serviço do Drive não disponível.', 503)
        
        # Configura o drive manager
        document_worker.set_drive_manager(drive_manager)
        
        # Inicia o worker
        document_worker.start()
        
        return api_success({
            'message': 'Worker de análise iniciado',
            'interval': document_worker.interval,
            'running': document_worker.running
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/worker/status', methods=['GET'])
def api_worker_status():
    """Retorna o status do worker"""
    try:
        return api_success({
            'running': document_worker.running,
            'interval': document_worker.interval,
            'pending_count': analysis_queue.get_pending_count()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

@app.route('/api/worker/progress', methods=['GET'])
def api_worker_progress():
    """Retorna o progresso do scanner em tempo real"""
    try:
        progress_data = scan_progress.get_status()
        return api_success(progress_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_error(str(e))

if __name__ == '__main__':
    # Cria a pasta de templates se não existir
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 60)
    print("🚀 Iniciando Painel de Comando")
    print("=" * 60)
    
    # Inicializa o banco de dados da fila
    print("📊 Inicializando banco de dados de análise...")
    analysis_queue.init_db()
    
    # Inicia o worker de análise em background
    print("🤖 Iniciando worker de análise de documentos...")
    # O worker será configurado após a primeira autenticação
    # document_worker.set_drive_manager(drive_manager)
    # document_worker.start()
    
    print("=" * 60)
    print("🌐 Servidor Web")
    print("=" * 60)
    print("📍 Home:   http://localhost:5000")
    print("📧 Gmail:  http://localhost:5000/gmail")
    print("📊 Sheets: http://localhost:5000/sheets")
    print("📁 Drive:  http://localhost:5000/drive")
    print("=" * 60)
    print("💡 O worker de análise será ativado após primeira autenticação")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

