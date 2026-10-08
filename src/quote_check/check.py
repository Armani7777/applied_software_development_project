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


def match_span(page_text: str, quote: str):
    """Индексы цитаты в исходном тексте страницы, если она там есть.

    Пробелы и регистр схлопываются так же, как в проверке. Если буква
    после casefold разъезжается по длине, подсветку не возвращаю:
    лучше ничего не подсветить, чем подсветить соседнее слово.
    """
    needle = collapse(quote)
    if not needle or page_text is None:
        return None

    folded = []
    spans = []
    i = 0
    n = len(page_text)
    while i < n and page_text[i].isspace():
        i += 1
    prev_space = False
    while i < n:
        ch = page_text[i]
        if ch.isspace():
            if folded and not prev_space:
                folded.append(" ")
                spans.append(i)
                prev_space = True
            i += 1
            continue
        prev_space = False
        folded_ch = ch.casefold()
        if len(folded_ch) != 1:
            return None
        folded.append(folded_ch)
        spans.append(i)
        i += 1
    while folded and folded[-1] == " ":
        folded.pop()
        spans.pop()

    hay = "".join(folded)
    at = hay.find(needle)
    if at < 0:
        return None
    start = spans[at]
    end = spans[at + len(needle) - 1] + 1
    return start, end


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
