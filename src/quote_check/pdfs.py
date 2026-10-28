"""Достать текст страниц из PDF. Без pypdf загрузка файла не работает."""

from io import BytesIO


def pages_from_pdf(data: bytes) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("Для PDF нужен пакет pypdf") from error
    reader = PdfReader(BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text.strip()))
    if not pages:
        raise ValueError("В PDF нет текстового слоя")
    return pages
