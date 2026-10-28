"""Черновик, чат и цитаты только из библиотеки. Свободную модель не вызываю."""

from __future__ import annotations

from quote_check.check import field_status
from quote_check.library import Hit, Library, Paper, split_sentences


DEMO_DRAFT = (
    "Интеллектуальный помощник для сопровождения научно-исследовательской работы\n\n"
    "## Зачем это\n"
    "Мне нужен не поиск статей, а место, где черновик главы собирается из работ, которые я сам положил в библиотеку. "
    "Если помощник ходит в интернет, он легко ставит ссылку на то, чего в PDF нет.\n\n"
    "## Что уже видно по источникам\n"
)


def verify_hit(library: Library, hit: Hit) -> dict:
    paper = library.papers[hit.paper_id]
    page_text = next((t for n, t in paper.pages if n == hit.page), "")
    status = field_status(page_text, hit.sentence, hit.page)
    return {
        **hit.to_dict(),
        "status": status["status"],
        "found": status["found"],
    }


def bibliography(library: Library, paper_ids: list[str]) -> list[str]:
    lines = []
    seen = set()
    for pid in paper_ids:
        paper = library.papers.get(pid)
        if not paper or paper.id in seen:
            continue
        seen.add(paper.id)
        lines.append(paper.apa())
    return lines


def continue_writing(library: Library, draft: str) -> dict:
    query = (draft or "").strip()[-500:] or "исследовательский вопрос карточка цитата страница"
    hits = library.search(query, limit=4)
    if not hits:
        return {
            "text": "В библиотеке нет кусков, похожих на конец черновика. Добавьте статью или уточните абзац.",
            "hits": [],
            "bibliography": [],
        }
    chunks = []
    for hit in hits[:3]:
        checked = verify_hit(library, hit)
        mark = "цитата на странице есть" if checked["found"] else "на этой странице фразы нет"
        quote = hit.sentence.rstrip(".")
        chunks.append(
            f"{hit.cite} отмечают: «{quote}» (с. {hit.page}, {mark})."
        )
    text = " ".join(chunks)
    text += " Эти фрагменты я оставляю в черновике только с тем статусом, который вернула проверка страницы."
    return {
        "text": text,
        "hits": [verify_hit(library, h) for h in hits],
        "bibliography": bibliography(library, [h.paper_id for h in hits]),
    }


def chat(library: Library, question: str) -> dict:
    q = (question or "").strip()
    if not q:
        return {"text": "Напишите вопрос к вашим статьям.", "hits": [], "bibliography": []}
    hits = library.search(q, limit=5)
    if not hits:
        return {
            "text": "В загруженных работах этого нет. Я не додумываю статью снаружи: либо добавьте PDF, либо смените вопрос.",
            "hits": [],
            "bibliography": [],
        }
    lines = ["По вашим статьям, без внешних источников:"]
    for i, hit in enumerate(hits, 1):
        checked = verify_hit(library, hit)
        flag = "cited" if checked["found"] else "unchecked"
        lines.append(f"{i}. {hit.cite}, с. {hit.page} [{flag}]: {hit.sentence}")
    lines.append("Если статус unchecked, в главу это лучше не тащить как готовую цитату.")
    return {
        "text": "\n".join(lines),
        "hits": [verify_hit(library, h) for h in hits],
        "bibliography": bibliography(library, [h.paper_id for h in hits]),
    }


def outline(library: Library, topic: str) -> dict:
    query = (topic or "").strip() or "карточка цитата страница помощник библиотека"
    hits = library.search(query, limit=8)
    if not hits:
        hits = []
        for paper in library.papers.values():
            first = split_sentences(paper.pages[0][1])
            if first:
                hits.append(Hit(paper.id, paper.title, paper.authors, paper.year, paper.pages[0][0], first[0], 1.0, paper.cite_short()))
        hits = hits[:6]
    if not hits:
        return {"text": "Библиотека пустая. Сначала добавьте хотя бы одну статью.", "hits": [], "bibliography": []}
    sections = [
        ("1. Вопрос и граница", hits[:2]),
        ("2. Что уже умеют соседние инструменты", hits[2:4] or hits[:1]),
        ("3. Где карточка молча врёт", hits[4:6] or hits[-1:]),
        ("4. Что проверять в пилоте", hits[-2:] or hits[:1]),
    ]
    lines = ["План главы из библиотеки, не из головы модели:"]
    used = []
    for title, group in sections:
        lines.append(title)
        for hit in group:
            lines.append(f"— {hit.cite}: {hit.sentence}")
            used.append(hit)
    return {
        "text": "\n".join(lines),
        "hits": [verify_hit(library, h) for h in used],
        "bibliography": bibliography(library, [h.paper_id for h in used]),
    }


def paraphrase(library: Library, selection: str) -> dict:
    sel = (selection or "").strip()
    if len(sel) < 8:
        return {"text": "Выделите фразу в черновике или вставьте её в чат.", "hits": [], "bibliography": []}
    hits = library.search(sel, limit=3)
    if not hits:
        return {
            "text": "Похожего предложения в библиотеке нет. Пересказывать «от себя» я не буду: так снова появится ссылка без страницы.",
            "hits": [],
            "bibliography": [],
        }
    hit = hits[0]
    checked = verify_hit(library, hit)
    text = (
        f"Пересказ только из источника {hit.cite}. "
        f"На странице {hit.page} говорится, что {hit.sentence[0].lower() + hit.sentence[1:] if hit.sentence[:1].isupper() else hit.sentence} "
        f"Статус поля: {checked['status']}."
    )
    return {
        "text": text,
        "hits": [verify_hit(library, h) for h in hits],
        "bibliography": bibliography(library, [h.paper_id for h in hits]),
    }


def cite_for(library: Library, selection: str) -> dict:
    sel = (selection or "").strip()
    if not sel:
        return {"text": "Выделите место в тексте или опишите, что процитировать.", "hits": [], "bibliography": []}
    hits = library.search(sel, limit=4)
    if not hits:
        return {"text": "В библиотеке нет подходящего источника.", "hits": [], "bibliography": []}
    pieces = []
    for hit in hits:
        checked = verify_hit(library, hit)
        pieces.append(f"{hit.cite}, с. {hit.page} [{checked['status']}]")
    text = "Можно вставить: " + "; ".join(pieces) + "."
    return {
        "text": text,
        "hits": [verify_hit(library, h) for h in hits],
        "bibliography": bibliography(library, [h.paper_id for h in hits]),
        "inline": hits[0].cite,
    }


def autocomplete(library: Library, prefix: str) -> dict:
    prefix = (prefix or "").strip()
    if len(prefix) < 12:
        return {"text": "", "hits": [], "bibliography": []}
    return continue_writing(library, prefix)
