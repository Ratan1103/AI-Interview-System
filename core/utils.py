"""
Utility functions for the core app.
"""

import io


def extract_text_from_pdf(file) -> str:
    """
    Extract plain text from an uploaded PDF file.
    Uses pypdf (the maintained successor to PyPDF2).
    Falls back gracefully if extraction fails.
    """
    text = ""
    try:
        from pypdf import PdfReader
        # file may be an InMemoryUploadedFile; read bytes first
        file_bytes = file.read()
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        # Log but don't crash — user can still proceed with empty text
        print(f"[utils] PDF extraction error: {e}")
    return text.strip()
