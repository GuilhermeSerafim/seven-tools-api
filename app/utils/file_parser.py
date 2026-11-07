# seven_tools_api/app/utils/file_parser.py
from io import BytesIO
from typing import BinaryIO

import pdfplumber
from docx import Document


def extract_text_from_pdf(file: BinaryIO) -> str:
    text_parts = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file: BinaryIO) -> str:
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(file: BinaryIO, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file)
    elif content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return extract_text_from_docx(file)
    elif content_type.startswith("text/"):
        return file.read().decode("utf-8")
    else:
        raise ValueError(f"Unsupported file type: {content_type}")
