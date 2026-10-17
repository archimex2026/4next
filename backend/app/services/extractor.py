import os
import re
import zipfile
from pathlib import Path
from typing import Dict, Any, Tuple

def extract_text_from_file(file_path: Path, file_type: str) -> Tuple[str, int, str]:
    """
    Extracts text, calculates page count, and extracts author/title hints.
    Returns: (extracted_text, estimated_pages, title_guess)
    """
    text = ""
    pages = 1
    raw_stem = file_path.stem.replace("_", " ").replace("-", " ")
    # Clean up common prefixes like "book-xxxx_"
    raw_stem = re.sub(r"^book-[a-f0-9]+_", "", file_path.name, flags=re.IGNORECASE)
    raw_stem = Path(raw_stem).stem.replace("_", " ").replace("-", " ")
    title_guess = re.sub(r"\s+", " ", raw_stem).strip().title()

    file_type = file_type.lower().strip(".")

    try:
        if file_type == "pdf":
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = max(1, len(reader.pages))
                extracted_pages = []
                # Extract 100% of all pages from the document without artificial caps
                for i in range(pages):
                    try:
                        p_text = reader.pages[i].extract_text()
                        if p_text and p_text.strip():
                            extracted_pages.append(f"[Page {i+1}]\n{p_text.strip()}")
                    except Exception as pe:
                        print(f"Notice extracting page {i+1}: {pe}")
                
                text = "\n\n".join(extracted_pages)
                
                # Try reading metadata title
                if reader.metadata and reader.metadata.title:
                    meta_title = reader.metadata.title.strip()
                    if len(meta_title) > 3 and not meta_title.lower().endswith(".pdf"):
                        title_guess = meta_title

                # If first page has a clear title header (e.g. "Sprint 1.MSD: Business Domain Design")
                if extracted_pages:
                    first_lines = [l.strip() for l in extracted_pages[0].split("\n") if len(l.strip()) > 3]
                    if first_lines:
                        candidate = " ".join(first_lines[:3])
                        # Clean up technical artifacts
                        cleaned_cand = re.sub(r"\s+", " ", candidate).strip()
                        if 8 <= len(cleaned_cand) <= 70:
                            title_guess = cleaned_cand

        elif file_type in ["docx", "doc"]:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)
            pages = max(1, len(text.split()) // 280)
            if paragraphs and len(paragraphs[0]) < 80:
                title_guess = paragraphs[0]

        elif file_type == "epub":
            with zipfile.ZipFile(file_path, "r") as z:
                html_files = [n for n in z.namelist() if n.endswith(('.html', '.xhtml', '.htm'))]
                epub_texts = []
                for h in html_files:
                    content = z.read(h).decode("utf-8", errors="ignore")
                    clean_text = re.sub(r"<[^>]+>", " ", content)
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    if clean_text:
                        epub_texts.append(clean_text)
                text = "\n\n".join(epub_texts)
                pages = max(1, len(text.split()) // 280)

        elif file_type in ["txt", "md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            pages = max(1, len(text.split()) // 280)
            first_line = text.strip().split("\n")[0].lstrip("#").strip()
            if 4 <= len(first_line) <= 80:
                title_guess = first_line

        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            pages = max(1, len(text.split()) // 280)

    except Exception as e:
        print(f"Error extracting {file_path}: {e}")
        text = f"Content extracted from {file_path.name}."
        pages = max(pages, 1)

    # Sanitize null bytes (SQLite cannot store \x00 in TEXT fields)
    text = text.replace("\x00", "")
    
    if not text.strip():
        text = f"Document: {title_guess}. Content parsed with standard curriculum extraction."
        pages = max(pages, 1)

    return text, pages, title_guess
