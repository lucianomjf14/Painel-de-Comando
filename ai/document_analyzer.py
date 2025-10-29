"""
Módulo de Análise Inteligente de Documentos
Utiliza Google Cloud Vision API para OCR e identificação real de documentos
"""

import re
import os
import io
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import tempfile

try:
    from google.cloud import vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("⚠️ Google Cloud Vision não disponível - usando análise básica")


class DocumentAnalyzer:
    """Classe para análise inteligente de documentos usando IA e OCR"""
    
    # Schema de padronização de nomenclatura

import re
import os
import io
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import tempfile
from googleapiclient.discovery import build
from auth.google_auth import google_auth

# Importações opcionais
try:
    from google.cloud import vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("⚠️ Google Cloud Vision não disponível - instale com: pip install google-cloud-vision")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2 não disponível - instale com: pip install PyPDF2")


class DocumentAnalyzer:
    """Classe para análise inteligente de documentos usando IA"""
    
    # Schema de padronização de nomenclatura
    DOCUMENT_SCHEMAS = {
        '01 - Documentos Pessoais': {
            'patterns': {
                'RG': r'(rg|identidade|carteira de identidade|registro geral)',
                'CPF': r'(cpf|cadastro de pessoa)',
                'CNH': r'(cnh|carteira nacional|habilitação|permissão.*dirigir)',
                'Titulo_Eleitor': r'(título|titulo eleitor)',
                'Comp_Residencia': r'(comprovante.{0,10}residência|endereço|comprovante.{0,10}endereço)',
                'Certidao_Nascimento': r'(certidão.{0,10}nascimento|cert.*nasc)',
                'Certidao_Casamento': r'(certidão.{0,10}casamento|cert.*casam)',
                'Carteira_Trabalho': r'(ctps|carteira.{0,10}trabalho)',
                'PIS_PASEP': r'(pis|pasep)',
                'Reservista': r'(reservista|certificado.{0,10}reservista)',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '02 - Documentos Admissionais e Periódicos': {
            'patterns': {
                'ASO_Admissional': r'aso.{0,10}admissional',
                'ASO_Periodico': r'aso.{0,10}periódico',
                'ASO_Demissional': r'aso.{0,10}demissional',
                'Exame_Admissional': r'exame.{0,10}admissional',
                'Exame_Periodico': r'exame.{0,10}periódico',
                'Atestado_Saude': r'atestado.{0,10}(saúde|ocupacional)',
                'Ficha_Registro': r'ficha.{0,10}registro',
                'Contrato_Trabalho': r'contrato.{0,10}trabalho',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '03 - Sinistros': {
            'patterns': {
                'CAT': r'(cat|comunicação.{0,10}acidente)',
                'Boletim_Ocorrencia': r'(b\.?o\.|boletim.{0,10}ocorrência)',
                'Laudo_Pericia': r'laudo.{0,10}perícia',
                'Atestado_Medico': r'atestado.{0,10}médico',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '04 - Férias': {
            'patterns': {
                'Aviso_Ferias': r'aviso.{0,10}férias',
                'Recibo_Ferias': r'recibo.{0,10}férias',
                'Concessao_Ferias': r'concessão.{0,10}férias',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '05 - Dependentes': {
            'patterns': {
                'CPF_Dependente': r'cpf.{0,10}(filho|filha|esposa|esposo|dependente)',
                'RG_Dependente': r'rg.{0,10}(filho|filha|esposa|esposo|dependente)',
                'Certidao_Nascimento_Dep': r'certidão.{0,10}nascimento.{0,10}(filho|filha)',
                'Certidao_Casamento': r'certidão.{0,10}casamento',
                'Carteira_Vacinacao': r'carteira.{0,10}vacinação',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '06 - Certificados': {
            'patterns': {
                'Certificado_Curso': r'certificado.{0,10}(curso|treinamento)',
                'Diploma': r'diploma',
                'Certificado_Digital': r'certificado.{0,10}digital',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '07 - IRPF': {
            'patterns': {
                'Declaracao_IRPF': r'(irpf|imposto.{0,10}renda|declaração.{0,10}imposto)',
                'Informe_Rendimentos': r'informe.{0,10}rendimentos',
                'Recibo_IRPF': r'recibo.{0,10}(irpf|imposto.{0,10}renda)',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '08 - Multas de Trânsito': {
            'patterns': {
                'Auto_Infracao': r'(auto.{0,10}infração|multa)',
                'Notificacao_Transito': r'notificação.{0,10}(trânsito|detran)',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '09 - Plano de Saúde': {
            'patterns': {
                'Carteirinha_Saude': r'carteirinha.{0,10}(saúde|plano)',
                'Contrato_Plano': r'contrato.{0,10}plano',
                'Declaracao_Beneficiario': r'declaração.{0,10}beneficiário',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '10 - Documentos Escaneados': {
            'patterns': {
                'Scan': r'(scan|digitalização|escaneado)',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '11 - Acordos': {
            'patterns': {
                'Acordo_Trabalhista': r'acordo.{0,10}trabalhista',
                'Termo_Acordo': r'termo.{0,10}acordo',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        },
        '12 - Rescisão': {
            'patterns': {
                'Termo_Rescisao': r'termo.{0,10}rescisão',
                'Aviso_Previo': r'aviso.{0,10}prévio',
                'Homologacao': r'homologação',
                'TRCT': r'(trct|termo.{0,10}rescisão.{0,10}contrato)',
            },
            'template': '{tipo}_{nome_completo}{validade}.{ext}'
        }
    }
    
    def __init__(self):
        """Inicializa o analisador de documentos"""
        self.use_google_vision = True  # Ativado para usar Google Vision API
        self.use_openai = False  # Pode ser ativado se tiver API key
        self.drive_service = None
        self.vision_client = None
        
        try:
            # Inicializa serviços
            from auth.google_auth import google_auth
            self.drive_service = google_auth.get_drive_service()
            
            # Tenta inicializar Google Vision API
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                print("✅ Google Vision API inicializada")
            except Exception as e:
                print(f"⚠️ Google Vision API não disponível: {e}")
                self.use_google_vision = False
                
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Document Analyzer: {e}")
    
    def download_file_content(self, file_id: str) -> Optional[bytes]:
        """Download do conteúdo do arquivo do Google Drive"""
        try:
            import io
            from googleapiclient.http import MediaIoBaseDownload
            
            request = self.drive_service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True
            )
            
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_stream.getvalue()
            
        except Exception as e:
            print(f"Erro ao baixar arquivo {file_id}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extrai texto de um PDF"""
        try:
            import io
            try:
                import PyPDF2
                
                pdf_file = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text = ""
                # Extrai texto das primeiras 3 páginas (suficiente para identificação)
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
            except ImportError:
                print("⚠️ PyPDF2 não instalado, usando método alternativo")
                return ""
                
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def analyze_with_vision_api(self, image_content: bytes) -> str:
        """Analisa imagem/PDF com Google Vision API (OCR)"""
        if not self.use_google_vision or not self.vision_client:
            return ""
        
        try:
            image = vision.Image(content=image_content)
            
            # Detecta texto
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                return texts[0].description
            
            return ""
            
        except Exception as e:
            print(f"Erro ao analisar com Vision API: {e}")
            return ""
    
    def classify_document_by_content(self, text_content: str, folder_type: str) -> Tuple[str, float]:
        """
        Classifica documento baseado no CONTEÚDO REAL (não apenas nome)
        Usa IA para análise inteligente
        """
        if not text_content or len(text_content) < 50:
            return ('Desconhecido', 0.0)
        
        text_lower = text_content.lower()
        
        # Palavras-chave específicas por tipo de documento
        keywords_map = {
            'RG': ['identidade', 'rg', 'registro geral', 'carteira de identidade', 'ssp'],
            'CPF': ['cpf', 'cadastro de pessoa física', 'receita federal'],
            'CNH': ['cnh', 'habilitação', 'detran', 'carteira nacional'],
            'ASO_Admissional': ['aso', 'atestado de saúde ocupacional', 'admissional', 'apto para o trabalho'],
            'ASO_Periodico': ['aso', 'periódico', 'exame médico periódico'],
            'Certidao_Nascimento': ['certidão', 'nascimento', 'cartório', 'nascido'],
            'Certidao_Casamento': ['certidão', 'casamento', 'cartório', 'cônjuge'],
            'CTPS': ['carteira de trabalho', 'ctps', 'ministério do trabalho'],
            'CAT': ['cat', 'comunicação de acidente', 'acidente de trabalho'],
            'Declaracao_IRPF': ['irpf', 'imposto de renda', 'declaração', 'receita federal'],
            'Informe_Rendimentos': ['informe de rendimentos', 'rendimentos', 'fonte pagadora'],
        }
        
        best_match = None
        best_score = 0.0
        
        for doc_type, keywords in keywords_map.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    # Peso baseado no tamanho da palavra-chave
                    weight = len(keyword.split()) / len(keywords)
                    score += weight
            
            # Normaliza score
            score = min(score / len(keywords), 1.0)
            
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Confiança mínima de 0.3 para considerar válido
        if best_score < 0.3:
            return ('Desconhecido', best_score)
        
        return (best_match or 'Desconhecido', best_score)
    
    def identify_document_type(self, filename: str, folder_type: str) -> Tuple[str, float]:
        """
        Identifica o tipo de documento baseado no nome do arquivo e pasta
        
        Args:
            filename: Nome do arquivo
            folder_type: Tipo da pasta (ex: "01 - Documentos Pessoais")
        
        Returns:
            Tupla (tipo_identificado, confiança)
        """
        if folder_type not in self.DOCUMENT_SCHEMAS:
            return ('Desconhecido', 0.0)
        
        patterns = self.DOCUMENT_SCHEMAS[folder_type]['patterns']
        filename_lower = filename.lower()
        
        best_match = None
        best_confidence = 0.0
        
        for doc_type, pattern in patterns.items():
            if re.search(pattern, filename_lower, re.IGNORECASE):
                # Calcula confiança baseada na qualidade do match
                confidence = 0.8 if pattern in filename_lower else 0.6
                
                if confidence > best_confidence:
                    best_match = doc_type
                    best_confidence = confidence
        
        return (best_match or 'Desconhecido', best_confidence)
    
    def extract_employee_info(self, filename: str) -> Dict[str, str]:
        """
        Extrai informações do funcionário do nome do arquivo
        
        Returns:
            Dict com: codigo, nome, ano, data, etc.
        """
        info = {}
        
        # Extrai ano (4 dígitos)
        year_match = re.search(r'\b(20\d{2})\b', filename)
        if year_match:
            info['ano'] = year_match.group(1)
        
        # Extrai data (vários formatos)
        date_patterns = [
            r'(\d{2}[-/]\d{2}[-/]\d{4})',
            r'(\d{4}[-/]\d{2}[-/]\d{2})'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, filename)
            if date_match:
                info['data'] = date_match.group(1).replace('/', '-')
                break
        
        # Extrai nome do funcionário (após " - ")
        name_match = re.search(r'-\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ][a-záàâãéèêíïóôõöúçñ\s]+)\.', filename)
        if name_match:
            info['nome_func'] = name_match.group(1).strip()
        
        return info
    
    def generate_standardized_name(self, 
                                   doc_type: str, 
                                   folder_type: str,
                                   employee_code: str,
                                   employee_name: str,
                                   original_filename: str) -> str:
        """
        Gera nome padronizado para o documento
        
        Args:
            doc_type: Tipo do documento identificado
            folder_type: Tipo da pasta
            employee_code: Código do funcionário
            employee_name: Nome do funcionário
            original_filename: Nome original do arquivo
        
        Returns:
            Nome padronizado do arquivo
        """
        if folder_type not in self.DOCUMENT_SCHEMAS:
            return original_filename
        
        template = self.DOCUMENT_SCHEMAS[folder_type].get('template', '{tipo}_{nome_func}.pdf')
        
        # Extrai informações adicionais do nome original
        info = self.extract_employee_info(original_filename)
        
        # Limpa nome do funcionário (apenas palavras principais)
        nome_limpo = self._clean_employee_name(employee_name)
        
        # Extensão do arquivo
        ext = os.path.splitext(original_filename)[1]
        
        # Preenche template
        try:
            new_name = template.format(
                tipo=doc_type,
                codigo_func=employee_code,
                nome_func=nome_limpo,
                ano=info.get('ano', ''),
                data=info.get('data', datetime.now().strftime('%Y-%m-%d')),
                periodo=info.get('periodo', ''),
                nome_dependente=info.get('nome_dependente', '')
            )
            
            # Remove campos vazios
            new_name = re.sub(r'_{2,}', '_', new_name)
            new_name = new_name.strip('_')
            
            # Adiciona extensão
            if not new_name.endswith(ext):
                new_name += ext
            
            return new_name
            
        except KeyError as e:
            print(f"Erro ao gerar nome: {e}")
            return original_filename
    
    def _clean_employee_name(self, full_name: str) -> str:
        """
        Limpa e formata nome do funcionário para nomenclatura
        Remove preposições e mantém apenas nome e sobrenome principais
        """
        # Remove código (números no início)
        name = re.sub(r'^\d+\s*-\s*', '', full_name)
        
        # Palavras a remover
        prepositions = ['de', 'da', 'do', 'dos', 'das', 'e']
        
        words = name.split()
        filtered_words = []
        
        for i, word in enumerate(words):
            # Mantém primeira e última palavra sempre
            if i == 0 or i == len(words) - 1:
                filtered_words.append(word)
            # Remove preposições do meio
            elif word.lower() not in prepositions:
                filtered_words.append(word)
        
        # Limita a 3 palavras
        if len(filtered_words) > 3:
            filtered_words = [filtered_words[0], filtered_words[-1]]
        
        return '_'.join(filtered_words)
    
    def analyze_folder_documents(self, 
                                 documents: List[Dict],
                                 folder_type: str,
                                 employee_code: str,
                                 employee_name: str) -> List[Dict[str, Any]]:
        """
        Analisa todos os documentos de uma pasta e sugere padronização
        USA ANÁLISE REAL DO CONTEÚDO COM IA (não apenas nome do arquivo)
        
        Returns:
            Lista de dicts com: 
            - file_id
            - original_name
            - identified_type
            - confidence
            - suggested_name
            - action (rename/move/keep)
            - extracted_text (preview)
        """
        results = []
        
        print(f"\n🔍 Analisando {len(documents)} documentos em '{folder_type}'...")
        
        for idx, doc in enumerate(documents, 1):
            filename = doc.get('name', '')
            file_id = doc.get('id', '')
            mime_type = doc.get('mimeType', '')
            
            print(f"   [{idx}/{len(documents)}] {filename}...")
            
            # Ignora arquivos de sistema
            if filename.lower() in ['desktop.ini', 'thumbs.db', '.ds_store']:
                print(f"      ⏭️ Arquivo de sistema, ignorado")
                continue
            
            # Baixa e analisa conteúdo REAL do arquivo
            doc_type = 'Desconhecido'
            confidence = 0.0
            extracted_text_preview = ''
            
            try:
                # Download do arquivo
                content = self.download_file_content(file_id)
                
                if content:
                    extracted_text = ''
                    
                    # Extrai texto baseado no tipo
                    if 'pdf' in mime_type.lower():
                        extracted_text = self.extract_text_from_pdf(content)
                        
                        # Se PDF não tem texto (pode ser imagem), usa OCR
                        if len(extracted_text) < 100 and self.use_google_vision:
                            print(f"      📸 PDF sem texto, usando OCR...")
                            extracted_text = self.analyze_with_vision_api(content)
                    
                    elif 'image' in mime_type.lower() and self.use_google_vision:
                        print(f"      📸 Imagem, usando OCR...")
                        extracted_text = self.analyze_with_vision_api(content)
                    
                    # Classifica baseado no CONTEÚDO REAL
                    if extracted_text:
                        doc_type, confidence = self.classify_document_by_content(extracted_text, folder_type)
                        extracted_text_preview = extracted_text[:200]  # Preview
                        print(f"      ✅ Identificado: {doc_type} (confiança: {confidence:.2f})")
                    else:
                        print(f"      ⚠️ Não foi possível extrair texto")
                        # Fallback: analisa pelo nome
                        doc_type, confidence = self.identify_document_type(filename, folder_type)
                        confidence = confidence * 0.5  # Reduz confiança pois é só pelo nome
                        print(f"      📝 Classificação por nome: {doc_type} (confiança: {confidence:.2f})")
                
                else:
                    print(f"      ❌ Erro ao baixar arquivo")
                    # Fallback: analisa pelo nome
                    doc_type, confidence = self.identify_document_type(filename, folder_type)
                    confidence = confidence * 0.5
                    
            except Exception as e:
                print(f"      ❌ Erro na análise: {e}")
                # Fallback: analisa pelo nome
                doc_type, confidence = self.identify_document_type(filename, folder_type)
                confidence = confidence * 0.5
            
            # Gera nome sugerido
            suggested_name = self.generate_standardized_name(
                doc_type,
                folder_type,
                employee_code,
                employee_name,
                filename
            )
            
            # Determina ação
            action = 'keep' if filename == suggested_name else 'rename'
            
            results.append({
                'file_id': file_id,
                'original_name': filename,
                'identified_type': doc_type,
                'confidence': confidence,
                'suggested_name': suggested_name,
                'action': action,
                'folder_type': folder_type,
                'extracted_text_preview': extracted_text_preview,
                'mime_type': mime_type
            })
        
        print(f"   ✅ Análise concluída: {len(results)} documentos processados\n")
        return results
    
    def analyze_employee_documents(self,
                                   employee_folders: List[Dict],
                                   employee_code: str,
                                   employee_name: str) -> Dict[str, Any]:
        """
        Analisa todos os documentos de um funcionário em todas as pastas
        
        Returns:
            Relatório completo com sugestões de padronização
        """
        report = {
            'employee_code': employee_code,
            'employee_name': employee_name,
            'total_files': 0,
            'files_to_rename': 0,
            'files_ok': 0,
            'by_folder': {},
            'suggestions': []
        }
        
        for folder in employee_folders:
            folder_name = folder['name']
            folder_id = folder['id']
            
            # Aqui você chamaria a API para listar arquivos da pasta
            # Por enquanto, retorna estrutura preparada
            
            report['by_folder'][folder_name] = {
                'total': 0,
                'to_rename': 0,
                'suggestions': []
            }
        
        return report


# Instância global
document_analyzer = DocumentAnalyzer()
