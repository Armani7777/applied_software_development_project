"""Проверка, что цитата и правда есть на указанной странице.

Модуль ничего не знает про нейросеть. Он получает уже извлечённый текст
страницы и строку, которую карточка хочет показать как цитату.
"""

import re


def collapse(text: str) -> str:
    """Склеивает пробелы и переносы, чтобы цитата не ломалась из-за вёрстки."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip().casefold()


def quote_found(page_text: str, quote: str) -> bool:
    """True, если цитата встречается в тексте страницы.

    Пустая цитата не считается найденной: иначе поле карточки можно
    закрыть, ничего не указав.
    """
    needle = collapse(quote)
    if not needle:
        return False
    return needle in collapse(page_text)


def field_status(page_text: str, quote: str, page: int) -> dict:
    """Статус одного поля карточки.

    cited — цитата есть на странице.
    unchecked — цитата указана, но на этой странице её нет.
    empty — цитату забыли вписать.
    """
    if not collapse(quote):
        status = "empty"
        found = False
    elif quote_found(page_text, quote):
        status = "cited"
        found = True
    else:
        status = "unchecked"
        found = False
    return {"page": page, "found": found, "status": status}
