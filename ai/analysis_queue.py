"""
Sistema de Análise Contínua de Documentos
Monitora, analisa e notifica sobre documentos que precisam de padronização
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import threading
import time


class DocumentAnalysisQueue:
    """Gerencia fila de análise de documentos"""
    
    def __init__(self, db_path='document_analysis.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Inicializa banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de documentos pendentes de análise
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                employee_code TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                folder_type TEXT NOT NULL,
                drive_id TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Tabela de sugestões de renomeação
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rename_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                original_name TEXT NOT NULL,
                suggested_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                employee_code TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                folder_type TEXT NOT NULL,
                drive_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                extracted_text TEXT,
                expiry_date TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at TIMESTAMP,
                UNIQUE(file_id)
            )
        ''')
        
        # Tabela de histórico de processamento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de documentos já analisados (cache)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyzed_cache (
                file_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                modified_time TEXT,
                last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                needs_rename BOOLEAN DEFAULT 0,
                employee_code TEXT,
                folder_type TEXT
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_status ON rename_suggestions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_employee ON rename_suggestions(employee_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_status ON pending_analysis(status)')
        
        conn.commit()
        conn.close()
        
        print("✅ Banco de dados de análise inicializado")
    
    def add_to_queue(self, file_id: str, file_name: str, employee_code: str, 
                     employee_name: str, folder_type: str, drive_id: str) -> bool:
        """Adiciona documento à fila de análise"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO pending_analysis 
                (file_id, file_name, employee_code, employee_name, folder_type, drive_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_id, file_name, employee_code, employee_name, folder_type, drive_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar à fila: {e}")
            return False
    
    def get_pending_documents(self, limit: int = 10) -> List[Dict]:
        """Retorna documentos pendentes de análise"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM pending_analysis 
            WHERE status = 'pending' 
            ORDER BY added_at ASC 
            LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def mark_as_processed(self, file_id: str):
        """Marca documento como processado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pending_analysis 
            SET status = 'processed' 
            WHERE file_id = ?
        ''', (file_id,))
        
        conn.commit()
        conn.close()
    
    def save_suggestion(self, suggestion: Dict) -> bool:
        """Salva sugestão de renomeação"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rename_suggestions 
                (file_id, original_name, suggested_name, document_type, 
                 employee_code, employee_name, folder_type, drive_id, 
                 confidence, extracted_text, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                suggestion['file_id'],
                suggestion['original_name'],
                suggestion['suggested_name'],
                suggestion.get('identified_type', 'Desconhecido'),
                suggestion['employee_code'],
                suggestion['employee_name'],
                suggestion['folder_type'],
                suggestion['drive_id'],
                suggestion.get('confidence', 0.0),
                suggestion.get('extracted_text', ''),
                suggestion.get('expiry_date', '')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar sugestão: {e}")
            return False
    
    def get_pending_suggestions(self, employee_code: str = None) -> List[Dict]:
        """Retorna sugestões pendentes de aprovação"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if employee_code:
            cursor.execute('''
                SELECT * FROM rename_suggestions 
                WHERE status = 'pending' AND employee_code = ?
                ORDER BY analyzed_at DESC
            ''', (employee_code,))
        else:
            cursor.execute('''
                SELECT * FROM rename_suggestions 
                WHERE status = 'pending'
                ORDER BY analyzed_at DESC
            ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_pending_count(self) -> int:
        """Retorna quantidade de sugestões pendentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM rename_suggestions WHERE status = "pending"')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_pending_by_employee(self) -> List[Dict]:
        """Retorna sugestões agrupadas por funcionário"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                employee_code,
                employee_name,
                COUNT(*) as pending_count,
                MIN(analyzed_at) as oldest_suggestion,
                MAX(analyzed_at) as newest_suggestion
            FROM rename_suggestions 
            WHERE status = 'pending'
            GROUP BY employee_code, employee_name
            ORDER BY pending_count DESC
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def approve_suggestion(self, suggestion_id: int, approved_by: str = 'system') -> bool:
        """Aprova uma sugestão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE rename_suggestions 
                SET status = 'approved', 
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, suggestion_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao aprovar sugestão: {e}")
            return False
    
    def reject_suggestion(self, suggestion_id: int) -> bool:
        """Rejeita uma sugestão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE rename_suggestions 
                SET status = 'rejected'
                WHERE id = ?
            ''', (suggestion_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao rejeitar sugestão: {e}")
            return False
    
    def log_processing(self, file_id: str, action: str, details: str = ''):
        """Registra ação no log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processing_log (file_id, action, details)
                VALUES (?, ?, ?)
            ''', (file_id, action, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao registrar log: {e}")
    
    def get_suggestion(self, suggestion_id: int) -> Dict:
        """Busca uma sugestão específica por ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM rename_suggestions WHERE id = ?', (suggestion_id,))
        result = cursor.fetchone()
        
        conn.close()
        return dict(result) if result else None
    
    def update_suggestion_status(self, suggestion_id: int, status: str) -> bool:
        """Atualiza o status de uma sugestão"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE rename_suggestions 
                SET status = ?
                WHERE id = ?
            ''', (status, suggestion_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False
    
    def is_already_analyzed(self, file_id: str, modified_time: str = None) -> bool:
        """
        Verifica se um documento já foi analisado
        
        Args:
            file_id: ID do arquivo
            modified_time: Data de modificação do arquivo (opcional)
        
        Returns:
            True se já foi analisado e não precisa reanalisar
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT modified_time FROM analyzed_cache WHERE file_id = ?', (file_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            return False
        
        # Se tem modified_time, verifica se mudou
        if modified_time and result[0] != modified_time:
            return False
        
        return True
    
    def mark_as_analyzed(self, file_id: str, file_name: str, modified_time: str = None, 
                         needs_rename: bool = False, employee_code: str = None, 
                         folder_type: str = None):
        """Marca documento como analisado no cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO analyzed_cache 
                (file_id, file_name, modified_time, needs_rename, employee_code, folder_type, last_analyzed)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (file_id, file_name, modified_time, needs_rename, employee_code, folder_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao marcar como analisado: {e}")
    
    def get_analyzed_count(self) -> int:
        """Retorna quantidade total de documentos já analisados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM analyzed_cache')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def init_db(self):
        """Alias para init_database (compatibilidade)"""
        self.init_database()


# Instância global
analysis_queue = DocumentAnalysisQueue()
