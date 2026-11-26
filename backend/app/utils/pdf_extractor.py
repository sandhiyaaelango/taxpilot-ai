import os
from typing import Tuple, Dict, Any
from app.config.logging import get_logger

logger = get_logger("pdf_extractor")

def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extracts text from a PDF using PyMuPDF (fitz) if available,
    with an automatic fallback to pure-Python pypdf/pdfminer when native DLLs are restricted.
    
    Detects scanned PDFs where extracted text is insufficient and flags ocr_required.
    """
    extracted_text = ""
    page_count = 0
    method = "unknown"
    error_detail = None

    # Try PyMuPDF (fitz) first
    try:
        import fitz
        doc = fitz.open(file_path)
        page_count = len(doc)
        text_parts = []
        for i in range(page_count):
            text_parts.append(doc[i].get_text())
        extracted_text = "\n".join(text_parts).strip()
        method = "pymupdf"
        doc.close()
    except Exception as e:
        logger.warning("pymupdf_failed_falling_back_to_pypdf", error=str(e))
        error_detail = str(e)
        
        # Fallback to pure-Python pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            page_count = len(reader.pages)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            extracted_text = "\n".join(text_parts).strip()
            method = "pypdf"
        except Exception as e2:
            logger.error("pypdf_fallback_failed", error=str(e2))
            
            # Fallback to pdfminer.six
            try:
                from pdfminer.high_level import extract_text as pdfminer_extract
                extracted_text = pdfminer_extract(file_path).strip()
                method = "pdfminer"
            except Exception as e3:
                logger.error("all_pdf_extractors_failed", error=str(e3))
                return {
                    "text": "",
                    "page_count": 0,
                    "is_scanned": True,
                    "ocr_required": True,
                    "method": "failed",
                    "error": f"Extraction failed: {e3}"
                }

    clean_text = extracted_text.strip()
    is_scanned = len(clean_text) < 40  # Less than 40 chars across pages strongly indicates a scanned/rasterized PDF
    ocr_required = is_scanned

    return {
        "text": clean_text,
        "page_count": page_count,
        "is_scanned": is_scanned,
        "ocr_required": ocr_required,
        "method": method,
        "error": None
    }
