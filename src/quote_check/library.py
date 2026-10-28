"""Библиотека статей: текст по страницам, поиск кусков, карточка источника."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


STOP = {
    "и", "в", "во", "не", "на", "с", "со", "а", "но", "да", "или", "как", "что",
    "это", "для", "от", "по", "к", "ко", "из", "у", "о", "об", "при", "же", "ли",
    "бы", "то", "ты", "мы", "он", "она", "они", "the", "a", "an", "of", "to",
    "in", "on", "for", "and", "or", "is", "are", "be", "as", "by", "with",
}


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zа-яё0-9]+", (text or "").casefold())
    return {w for w in words if len(w) > 2 and w not in STOP}


def split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [s.strip() for s in raw if len(s.strip()) > 20]


def split_pages(text: str) -> list[tuple[int, str]]:
    """Если в тексте есть маркеры «стр. N», режу по ним. Иначе одна страница."""
    if not text or not text.strip():
        return []
    parts = re.split(r"(?m)^(?:---\s*)?(?:стр\.?|page)\s*(\d+)\s*:?\s*$", text.strip())
    if len(parts) == 1:
        return [(1, text.strip())]
    pages = []
    # split keeps the captured page numbers as separate items after the first chunk
    head = parts[0].strip()
    i = 1
    if head:
        pages.append((1, head))
    while i + 1 < len(parts):
        try:
            number = int(parts[i])
        except ValueError:
            number = len(pages) + 1
        pages.append((number, parts[i + 1].strip()))
        i += 2
    return [(n, t) for n, t in pages if t]


@dataclass
class Paper:
    id: str
    title: str
    authors: str
    year: str
    pages: list[tuple[int, str]] = field(default_factory=list)

    def full_text(self) -> str:
        return "\n".join(text for _, text in self.pages)

    def cite_short(self) -> str:
        names = [w for w in re.findall(r"[A-Za-zА-Яа-яЁё-]+", self.authors or "") if len(w) > 2]
        last = names[0] if names else "Без автора"
        return f"({last}, {self.year})" if self.year else f"({last})"

    def apa(self) -> str:
        return f"{self.authors} ({self.year}). {self.title}."

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "pages": [{"n": n, "text": t} for n, t in self.pages],
            "chars": len(self.full_text()),
        }


@dataclass
class Hit:
    paper_id: str
    title: str
    authors: str
    year: str
    page: int
    sentence: str
    score: float
    cite: str

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "page": self.page,
            "sentence": self.sentence,
            "score": round(self.score, 3),
            "cite": self.cite,
        }


class Library:
    def __init__(self) -> None:
        self.papers: dict[str, Paper] = {}
        self._n = 0

    def add(self, title: str, authors: str, year: str, text: str) -> Paper:
        pages = split_pages(text)
        if not pages:
            raise ValueError("Пустой текст статьи")
        self._n += 1
        paper = Paper(
            id=f"p{self._n}",
            title=(title or "Без названия").strip(),
            authors=(authors or "Неизвестный автор").strip(),
            year=(year or "").strip(),
            pages=pages,
        )
        self.papers[paper.id] = paper
        return paper

    def add_pages(self, title: str, authors: str, year: str, pages: list[tuple[int, str]]) -> Paper:
        cleaned = [(n, t.strip()) for n, t in pages if t and t.strip()]
        if not cleaned:
            raise ValueError("Из файла не получилось текста")
        self._n += 1
        paper = Paper(
            id=f"p{self._n}",
            title=(title or "Без названия").strip(),
            authors=(authors or "Неизвестный автор").strip(),
            year=(year or "").strip(),
            pages=cleaned,
        )
        self.papers[paper.id] = paper
        return paper

    def remove(self, paper_id: str) -> None:
        self.papers.pop(paper_id, None)

    def search(self, query: str, limit: int = 6) -> list[Hit]:
        q = tokens(query)
        if not q:
            return []
        hits: list[Hit] = []
        for paper in self.papers.values():
            for page, text in paper.pages:
                for sentence in split_sentences(text):
                    st = tokens(sentence)
                    if not st:
                        continue
                    overlap = len(q & st)
                    if overlap == 0:
                        continue
                    score = overlap / (len(q) ** 0.5)
                    hits.append(Hit(
                        paper_id=paper.id,
                        title=paper.title,
                        authors=paper.authors,
                        year=paper.year,
                        page=page,
                        sentence=sentence,
                        score=score,
                        cite=paper.cite_short(),
                    ))
        hits.sort(key=lambda h: (-h.score, h.page))
        seen = set()
        unique = []
        for hit in hits:
            key = (hit.paper_id, hit.sentence[:80])
            if key in seen:
                continue
            seen.add(key)
            unique.append(hit)
            if len(unique) >= limit:
                break
        return unique

    def to_list(self) -> list[dict]:
        return [p.to_dict() for p in self.papers.values()]


DEMO_PAPERS = [
    {
        "title": "Literature cards for master's research: a small assistant, not a search engine",
        "authors": "Nurbekova A., Suleimenov T.",
        "year": "2024",
        "text": (
            "стр. 1\n"
            "Магистрант теряет время не на поиск статьи, а на то, что после чтения неясно, "
            "зачем эта работа вообще лежала в папке. Карточка должна отвечать на исследовательский вопрос, "
            "а не пересказывать аннотацию.\n"
            "стр. 2\n"
            "Мы сравнивали Elicit и SciSpace на двадцати статьях по компьютерному зрению. "
            "Оба инструмента хорошо вытаскивают цель работы и плохо держат номер страницы у цитаты. "
            "Если фраза красивая, но её нет на указанной странице, карточку нельзя считать готовой.\n"
            "стр. 3\n"
            "В пилоте с девятью магистрантами поле «не проверено» оказалось полезнее, чем отдельная кнопка «ошибка». "
            "Пустая цитата и чужая фраза — разные случаи, их нельзя схлопывать в один статус."
        ),
    },
    {
        "title": "When retrieval-augmented writing invents a page number",
        "authors": "Kim J., Orlova M.",
        "year": "2025",
        "text": (
            "стр. 1\n"
            "Модели охотно ставят ссылку рядом с утверждением. Проверка по корпусу показывает, "
            "что часть ссылок ведёт на статью, где такого предложения нет.\n"
            "стр. 2\n"
            "Авторы пишут, что метрики PSNR и SSIM плохо совпадают с mAP, если сжатие JPEG "
            "считают достаточным прокси качества для детекции. Проверка шла на выборке COCO val2017.\n"
            "стр. 3\n"
            "Мы предлагаем не закрывать поле цитаты, пока строка не найдена на тексте страницы. "
            "Перенос слова с дефисом и цитата на стыке двух страниц остаются отдельными ограничениями, "
            "их нельзя чинить общим удалением всех дефисов."
        ),
    },
    {
        "title": "Writing with a private library: autocomplete that refuses outside sources",
        "authors": "Petrov D.",
        "year": "2023",
        "text": (
            "стр. 1\n"
            "Академический помощник, который ходит в открытый интернет, удобен и опасен: "
            "он подмешивает работы, которых исследователь не читал.\n"
            "стр. 2\n"
            "Ограничение библиотекой пользователя снижает полноту, но делает черновик проверяемым. "
            "Каждое продолжение абзаца должно опираться на предложение из загруженных PDF.\n"
            "стр. 3\n"
            "В интерфейсе это выглядит как редактор в центре, источники слева и чат справа. "
            "Кнопка «продолжить» не вызывает свободную генерацию, а собирает абзац из найденных кусков "
            "и сразу ставит статус цитаты cited или unchecked."
        ),
    },
]


def seed_library(library: Library) -> None:
    if library.papers:
        return
    for item in DEMO_PAPERS:
        library.add(item["title"], item["authors"], item["year"], item["text"])
