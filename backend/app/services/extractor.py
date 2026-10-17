"""Bounded extraction. Preserve real PDF pages; number text sections for other formats."""
import re
import zipfile
from statistics import median
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

MAX_TEXT_CHARACTERS = 1_000_000
MAX_PAGES = 500
MAX_ARCHIVE_BYTES = 40 * 1024 * 1024


class ExtractionError(ValueError):
    pass


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "h1", "h2", "h3", "li", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _clean(text):
    text = text.replace("\x00", "").replace("\r\n", "\n")
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()).strip()


def _bounded_archive(archive):
    entries = archive.infolist()
    if len(entries) > 1500 or sum(x.file_size for x in entries) > MAX_ARCHIVE_BYTES:
        raise ExtractionError("Arhiva este prea mare după decomprimare (maximum 40 MB / 1500 fișiere).")
    if any(x.file_size > 1_000_000 and x.file_size / max(1, x.compress_size) > 150 for x in entries):
        raise ExtractionError("Arhiva are un raport de compresie nesigur.")


def _text_sections(text):
    # ponytail: text formats have numbered sections, not invented physical pages.
    sections, current = [], ""
    for paragraph in re.split(r"\n\s*\n", text):
        for start in range(0, len(paragraph), 6000):
            part = paragraph[start:start + 6000]
            if current and len(current) + len(part) > 6000:
                sections.append(current)
                current = ""
            current += ("\n\n" if current else "") + part
    if current:
        sections.append(current)
    return [{"page": i + 1, "text": chunk} for i, chunk in enumerate(sections)]


def extract_document(file_path: Path, file_type: str) -> dict:
    kind = file_type.lower().lstrip(".")
    title, pages = "", []
    try:
        if kind == "pdf":
            import pdfplumber
            with pdfplumber.open(file_path, password="") as reader:
                if len(reader.pages) > MAX_PAGES:
                    raise ExtractionError("Documentul depășește limita de 500 de pagini.")
                total_characters = 0
                for index, page in enumerate(reader.pages):
                    # Faux bold prints the same glyph repeatedly. Removing duplicate
                    # glyphs fixes identifiers without deleting legitimate C++ operators.
                    body_size = median(c["size"] for c in page.chars) if page.chars else 12
                    def is_content(obj):
                        # Large diagonal draft watermarks cross otherwise readable prose.
                        matrix = obj.get("matrix", (1, 0, 0, 1))
                        return not (obj.get("object_type") == "char" and obj.get("size", 0) > body_size * 2.5
                                    and abs(matrix[1]) > .1 and abs(matrix[2]) > .1)
                    clean_page = page.filter(is_content).dedupe_chars(tolerance=1, extra_attrs=())
                    text = _clean(clean_page.extract_text(x_tolerance=2, y_tolerance=3) or "")
                    total_characters += len(text)
                    if total_characters > MAX_TEXT_CHARACTERS:
                        raise ExtractionError("Textul depășește limita de 1.000.000 de caractere. Împarte PDF-ul în părți.")
                    pages.append({"page": index + 1, "text": text})
                    page.close()
                title = str((reader.metadata or {}).get("Title") or "").strip()[:200]
        elif kind == "docx":
            with zipfile.ZipFile(file_path) as archive:
                _bounded_archive(archive)
            from docx import Document
            document = Document(file_path)
            paragraphs = [p.text for p in document.paragraphs]
            paragraphs.extend(" | ".join(cell.text for cell in row.cells) for table in document.tables for row in table.rows)
            pages = _text_sections(_clean("\n\n".join(paragraphs)))
        elif kind == "epub":
            with zipfile.ZipFile(file_path) as archive:
                _bounded_archive(archive)
                paths = [name for name in archive.namelist() if name.lower().endswith((".xhtml", ".html", ".htm"))]
                if "META-INF/container.xml" in archive.namelist():
                    container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
                    rootfile = container.find(".//{*}rootfile")
                    if rootfile is not None:
                        package_name = rootfile.attrib.get("full-path", "")
                        package = ElementTree.fromstring(archive.read(package_name))
                        manifest = {item.attrib.get("id"): item.attrib.get("href", "") for item in package.findall(".//{*}manifest/{*}item")}
                        import posixpath
                        ordered = [posixpath.normpath(posixpath.join(posixpath.dirname(package_name), manifest.get(item.attrib.get("idref"), ""))) for item in package.findall(".//{*}spine/{*}itemref")]
                        paths = [name for name in ordered if name in paths] or paths
                total_characters = 0
                for name in paths:
                    parser = _HTMLText()
                    parser.feed(archive.read(name).decode("utf-8", errors="replace"))
                    text = _clean(" ".join(parser.parts))
                    total_characters += len(text)
                    if total_characters > MAX_TEXT_CHARACTERS:
                        raise ExtractionError("Textul EPUB depășește limita de 1.000.000 de caractere.")
                    if text:
                        pages.extend(_text_sections(text))
                pages = [{"page": i + 1, "text": p["text"]} for i, p in enumerate(pages)]
        elif kind in {"txt", "md"}:
            pages = _text_sections(_clean(file_path.read_text(encoding="utf-8-sig")))
        else:
            raise ExtractionError("Format neacceptat. Folosește PDF, EPUB, DOCX, TXT sau MD. Convertește DOC în DOCX.")
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("Fișierul nu poate fi citit. Încarcă o copie validă, cu text selectabil.") from exc

    text = "\n\n".join(p["text"] for p in pages if p["text"])
    if len(text) > MAX_TEXT_CHARACTERS:
        raise ExtractionError("Textul depășește limita de 1.000.000 de caractere. Împarte documentul în părți.")
    if not re.search(r"[^\W\d_]", text, re.UNICODE):
        raise ExtractionError("Nu am găsit text selectabil. Pentru un PDF scanat, aplică OCR și încarcă-l din nou.")
    return {"text": text, "pages": pages, "page_count": len(pages), "title": title, "page_kind": "page" if kind == "pdf" else "section"}


def extract_text_from_file(file_path: Path, file_type: str):
    document = extract_document(file_path, file_type)
    return document["text"], document["page_count"], document["title"]
