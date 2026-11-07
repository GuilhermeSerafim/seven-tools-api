# seven_tools_api/tests/test_file_parsing.py
import io
from docx import Document

from app.utils.file_parser import extract_text_from_docx


def test_extract_text_from_docx():
    doc = Document()
    doc.add_paragraph("Proposta Comercial")
    doc.add_paragraph("Valor: R$ 15.000")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    text = extract_text_from_docx(buffer)
    assert "Proposta Comercial" in text
    assert "R$ 15.000" in text
