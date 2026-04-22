import os
from PyPDF2 import PdfReader
from docx import Document

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.txt', '.py']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif ext == '.docx':
            doc = Document(file_path)
            text = ''
            for para in doc.paragraphs:
                text += para.text + '\n'
            return text
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        raise ValueError(f"Error extracting text from {file_path}: {str(e)}")

def inject_attachment(prompt, extracted_text):
    return f"{prompt}\n\n<document>\n{extracted_text}\n</document>"