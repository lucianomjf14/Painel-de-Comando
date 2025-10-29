"""
Background Worker - Processa fila de análise de documentos
"""

import threading
import time
from typing import Optional, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ai.analysis_queue import analysis_queue
from ai.document_analyzer import document_analyzer


class ScanProgress:
    """Armazena progresso do scanner em tempo real"""
    
    def __init__(self):
        self.is_scanning = False
        self.total_employees = 0
        self.current_employee_index = 0
        self.current_employee_name = ""
        self.current_document = ""
        self.total_scanned = 0
        self.total_analyzed = 0
        self.total_suggestions = 0
        self.logs = []
        self.start_time = None
        self.lock = threading.Lock()
    
    def start(self):
        with self.lock:
            self.is_scanning = True
            self.total_employees = 0
            self.current_employee_index = 0
            self.current_employee_name = ""
            self.current_document = ""
            self.total_scanned = 0
            self.total_analyzed = 0
            self.total_suggestions = 0
            self.logs = []
            self.start_time = datetime.now()
    
    def finish(self):
        with self.lock:
            self.is_scanning = False
            self.current_employee_name = "Concluído"
            self.current_document = "Scanner finalizado"
    
    def add_log(self, message: str):
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] {message}")
            if len(self.logs) > 100:  # Mantém apenas últimas 100 linhas
                self.logs.pop(0)
    
    def get_status(self) -> Dict:
        with self.lock:
            progress = 0
            if self.total_employees > 0:
                progress = int((self.current_employee_index / self.total_employees) * 100)
            
            # Calcula velocidade de processamento
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            docs_per_second = self.total_analyzed / elapsed_seconds if elapsed_seconds > 0 else 0
            
            return {
                'is_scanning': self.is_scanning,
                'progress_percentage': progress,
                'total_employees': self.total_employees,
                'current_employee_index': self.current_employee_index,
                'current_employee_name': self.current_employee_name,
                'current_document': self.current_document,
                'total_scanned': self.total_scanned,
                'total_analyzed': self.total_analyzed,
                'total_suggestions': self.total_suggestions,
                'docs_per_second': round(docs_per_second, 2),
                'logs': self.logs[-20:] if self.logs else [],  # Últimas 20 linhas
                'elapsed_time': str(datetime.now() - self.start_time).split('.')[0] if self.start_time else "00:00:00",
                'already_analyzed_cache': analysis_queue.get_analyzed_count()
            }


# Instância global de progresso
scan_progress = ScanProgress()


class DocumentAnalysisWorker:
    """Worker que processa documentos em background"""
    
    def __init__(self, interval: int = 30, max_workers: int = 5):
        """
        Args:
            interval: Intervalo em segundos entre processamentos (padrão: 30s)
            max_workers: Número máximo de threads paralelas para análise (padrão: 5)
        """
        self.interval = interval
        self.max_workers = max_workers  # Processamento paralelo
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.drive_manager = None
        self.auto_scan_enabled = True
        self.drive_id = None
        self.employees_folder_id = None
        self.last_scan_time = None
        self.scan_interval = 300  # Re-escanear a cada 5 minutos para detectar novos arquivos
        self.metadata_cache = {}  # Cache de metadados de arquivos
        self.cache_lock = threading.Lock()
        
        # Arquivos de sistema para ignorar
        self.ignored_files = {
            'desktop.ini', 'thumbs.db', '.ds_store', 
            'icon\r', '.localized', '$recycle.bin'
        }
    
    def set_drive_manager(self, drive_manager):
        """Define o drive manager para download de arquivos"""
        self.drive_manager = drive_manager
    
    def configure_auto_scan(self, drive_id: str, employees_folder_id: str):
        """
        Configura scan automático
        
        Args:
            drive_id: ID do Drive compartilhado
            employees_folder_id: ID da pasta de funcionários
        """
        self.drive_id = drive_id
        self.employees_folder_id = employees_folder_id
        self.auto_scan_enabled = True
        print(f"✅ Auto-scan configurado para Drive: {drive_id}")
        print(f"⚡ Processamento paralelo: {self.max_workers} workers")
        
    def start(self):
        """Inicia o worker em background"""
        if self.running:
            print("⚠️ Worker já está rodando")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        print(f"✅ Worker de análise iniciado (intervalo: {self.interval}s)")
        
    def stop(self):
        """Para o worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Worker de análise parado")
        
    def _worker_loop(self):
        """Loop principal do worker"""
        while self.running:
            try:
                # Verifica se precisa fazer scan automático
                if self.auto_scan_enabled and self.drive_id and self.employees_folder_id:
                    current_time = time.time()
                    
                    # Primeiro scan ou passou do intervalo
                    if (self.last_scan_time is None or 
                        (current_time - self.last_scan_time) >= self.scan_interval):
                        
                        print(f"🔄 Iniciando scan automático...")
                        self.scan_employee_folders(self.drive_id, self.employees_folder_id)
                        self.last_scan_time = current_time
                
                # Processa documentos na fila
                self._process_batch()
                
            except Exception as e:
                print(f"❌ Erro no worker: {e}")
                import traceback
                traceback.print_exc()
            
            # Aguarda próximo ciclo
            time.sleep(self.interval)
    
    def _process_batch(self, batch_size: int = 5):
        """Processa um lote de documentos"""
        # Busca documentos pendentes
        pending = analysis_queue.get_pending_documents(limit=batch_size)
        
        if not pending:
            return  # Nada para processar
        
        print(f"📊 Processando {len(pending)} documento(s) pendente(s)...")
        
        for doc in pending:
            try:
                self._analyze_document(doc)
                analysis_queue.mark_as_processed(doc['file_id'])
                analysis_queue.log_processing(
                    doc['file_id'], 
                    'analyzed', 
                    f"Documento analisado automaticamente"
                )
            except Exception as e:
                print(f"❌ Erro ao analisar {doc['file_name']}: {e}")
                analysis_queue.log_processing(
                    doc['file_id'], 
                    'error', 
                    str(e)
                )
    
    def _analyze_document(self, doc: dict):
        """Analisa um documento específico"""
        # Atualiza progresso
        scan_progress.current_employee_name = f"{doc['employee_code']} - {doc['employee_name']}"
        scan_progress.current_document = doc['file_name']
        scan_progress.total_analyzed += 1
        
        # Identifica tipo de documento
        doc_type, confidence = document_analyzer.identify_document_type(
            doc['file_name'],
            doc['folder_type']
        )
        
        # Gera nome sugerido
        suggested_name = document_analyzer.generate_standardized_name(
            doc_type,
            doc['folder_type'],
            doc['employee_code'],
            doc['employee_name'],
            doc['file_name']
        )
        
        needs_rename = False
        
        # Se nome é diferente, cria sugestão
        if suggested_name != doc['file_name']:
            suggestion = {
                'file_id': doc['file_id'],
                'original_name': doc['file_name'],
                'suggested_name': suggested_name,
                'identified_type': doc_type,
                'employee_code': doc['employee_code'],
                'employee_name': doc['employee_name'],
                'folder_type': doc['folder_type'],
                'drive_id': doc['drive_id'],
                'confidence': confidence,
                'action': 'rename'
            }
            
            # Salva sugestão
            analysis_queue.save_suggestion(suggestion)
            scan_progress.total_suggestions += 1
            needs_rename = True
            
            log_msg = f"  ✅ Sugestão: {doc['file_name'][:30]}... → {suggested_name[:30]}..."
            scan_progress.add_log(log_msg)
            print(f"  ✅ Sugestão criada: {doc['file_name']} → {suggested_name}")
        else:
            print(f"  ⏭️ Arquivo já padronizado: {doc['file_name']}")
        
        # Marca como analisado no cache
        analysis_queue.mark_as_analyzed(
            file_id=doc['file_id'],
            file_name=doc['file_name'],
            modified_time=doc.get('modified_time'),
            needs_rename=needs_rename,
            employee_code=doc['employee_code'],
            folder_type=doc['folder_type']
        )
    
    def scan_employee_folders(self, drive_id: str, employees_folder_id: str):
        """
        Escaneia todas as pastas de funcionários e adiciona documentos à fila
        
        Args:
            drive_id: ID do Drive compartilhado
            employees_folder_id: ID da pasta de funcionários (ex: 1.1. Funcionários)
        """
        if not self.drive_manager:
            print("❌ Drive manager não configurado")
            return
        
        scan_progress.start()
        scan_progress.add_log("🔍 Iniciando scanner de documentos...")
        scan_progress.add_log(f"� Drive ID: {drive_id}")
        scan_progress.add_log(f"📂 Pasta Funcionários: {employees_folder_id}")
        
        print("�🔍 Iniciando scanner de documentos...")
        print(f"   Drive ID: {drive_id}")
        print(f"   Pasta Funcionários: {employees_folder_id}")
        
        try:
            # Lista todas as pastas de funcionários
            contents = self.drive_manager.list_files_in_shared_drive(
                drive_id, 
                parent_id=employees_folder_id
            )
            
            employee_folders = contents.get('folders', [])
            scan_progress.total_employees = len(employee_folders)
            
            log_msg = f"📁 Encontradas {len(employee_folders)} pastas de funcionários"
            scan_progress.add_log(log_msg)
            print(log_msg)
            
            total_documents = 0
            
            for idx, employee_folder in enumerate(employee_folders, 1):
                employee_name = employee_folder['name']
                employee_folder_id = employee_folder['id']
                
                # Extrai código do funcionário (ex: "1.0 - Nome" -> "1.0")
                employee_code = employee_name.split(' - ')[0] if ' - ' in employee_name else employee_name.split('.')[0]
                full_name = employee_name.split(' - ')[1] if ' - ' in employee_name else employee_name
                
                scan_progress.current_employee_index = idx
                scan_progress.current_employee_name = f"{employee_code} - {full_name}"
                
                log_msg = f"👤 [{idx}/{len(employee_folders)}] Processando: {employee_code} - {full_name}"
                scan_progress.add_log(log_msg)
                print(log_msg)
                
                # Lista subpastas do funcionário
                employee_contents = self.drive_manager.list_files_in_shared_drive(
                    drive_id,
                    parent_id=employee_folder_id
                )
                
                subfolders = employee_contents.get('folders', [])
                
                # Processa cada subpasta
                for subfolder in subfolders:
                    folder_name = subfolder['name']
                    folder_id = subfolder['id']
                    
                    scan_progress.current_document = f"Escaneando: {folder_name}"
                    
                    # Lista arquivos da pasta
                    folder_contents = self.drive_manager.list_files_in_shared_drive(
                        drive_id,
                        parent_id=folder_id
                    )
                    
                    files = folder_contents.get('files', [])
                    
                    # Adiciona cada arquivo à fila (se ainda não foi analisado)
                    for file in files:
                        file_id = file['id']
                        file_name = file['name']
                        modified_time = file.get('modifiedTime', '')
                        
                        # Verifica se já foi analisado
                        if analysis_queue.is_already_analyzed(file_id, modified_time):
                            continue  # Pula arquivo já analisado
                        
                        # Adiciona à fila
                        analysis_queue.add_to_queue(
                            file_id=file_id,
                            file_name=file_name,
                            employee_code=employee_code,
                            employee_name=full_name,
                            folder_type=folder_name,
                            drive_id=drive_id
                        )
                        total_documents += 1
                        scan_progress.total_scanned += 1
                        scan_progress.current_document = file_name
                    
                    if files:
                        new_files = total_documents - (scan_progress.total_scanned - len(files))
                        if new_files > 0:
                            log_msg = f"   📄 {folder_name}: {len(files)} arquivo(s), {new_files} novo(s)"
                            scan_progress.add_log(log_msg)
                            print(log_msg)
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.1)
            
            final_msg = f"✅ Scanner concluído: {total_documents} documento(s) adicionado(s) à fila"
            scan_progress.add_log(final_msg)
            scan_progress.add_log("🤖 Worker processará automaticamente a cada 30 segundos")
            print(final_msg)
            
            scan_progress.finish()
            
        except Exception as e:
            error_msg = f"❌ Erro ao escanear pastas: {e}"
            scan_progress.add_log(error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
            scan_progress.finish()


# Instância global do worker
document_worker = DocumentAnalysisWorker(interval=30)
