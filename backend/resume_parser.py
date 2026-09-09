"""
VagaMatch - Parser de currículos em PDF/DOCX
Extrai texto e informações estruturadas de arquivos de currículo
"""
import io
from typing import Dict, Optional, Tuple
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

import docx


def extrair_texto_pdf(arquivo_bytes: bytes) -> str:
    """Extrai texto de um arquivo PDF (bytes)."""
    try:
        pdf_file = io.BytesIO(arquivo_bytes)
        reader = PdfReader(pdf_file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto
    except Exception as e:
        print(f"[ERRO] Falha ao ler PDF: {e}")
        return ""


def extrair_texto_docx(arquivo_bytes: bytes) -> str:
    """Extrai texto de um arquivo DOCX (bytes)."""
    try:
        doc_file = io.BytesIO(arquivo_bytes)
        doc = docx.Document(doc_file)
        texto = ""
        for paragraph in doc.paragraphs:
            texto += paragraph.text + "\n"
        return texto
    except Exception as e:
        print(f"[ERRO] Falha ao ler DOCX: {e}")
        return ""


def extrair_texto_arquivo(filename: str, arquivo_bytes: bytes) -> str:
    """
    Detecta o tipo de arquivo e extrai o texto adequado.
    Suporta: .pdf, .docx, .doc, .txt
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extrair_texto_pdf(arquivo_bytes)
    elif ext in (".docx", ".doc"):
        return extrair_texto_docx(arquivo_bytes)
    elif ext == ".txt":
        try:
            return arquivo_bytes.decode("utf-8", errors="ignore")
        except:
            return arquivo_bytes.decode("latin-1", errors="ignore")
    else:
        raise ValueError(f"Formato não suportado: {ext}")


def processar_curriculo_upload(filename: str, arquivo_bytes: bytes) -> Dict:
    """
    Processa o upload de um currículo e retorna dados estruturados.
    """
    texto = extrair_texto_arquivo(filename, arquivo_bytes)

    if not texto.strip():
        raise ValueError("Não foi possível extrair texto do arquivo. Verifique o formato.")

    # Tentar identificar nome (primeira linha ou primeiras palavras)
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    nome = linhas[0] if linhas else "Candidato"

    # Limitar texto para processamento
    texto_limitado = texto[:5000]

    return {
        "nome": nome,
        "texto_completo": texto_limitado,
        "tamanho_arquivo": len(arquivo_bytes),
        "formato": Path(filename).suffix.lower()
    }
