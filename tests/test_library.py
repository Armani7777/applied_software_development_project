from quote_check.library import Library, seed_library, split_pages


def test_split_pages_keeps_numbers():
    pages = split_pages("стр. 1\nПервый абзац длиннее двадцати символов.\nстр. 3\nТретья страница тоже с запасом текста.")
    assert pages[0][0] == 1
    assert pages[1][0] == 3
    assert "Первый" in pages[0][1]


def test_search_finds_sentence_from_seed():
    library = Library()
    seed_library(library)
    hits = library.search("номер страницы у цитаты")
    assert hits
    assert any("страницы" in h.sentence.casefold() for h in hits)


def test_empty_library_search_is_empty():
    assert Library().search("цитата") == []


def test_short_cite_uses_surname_not_initial():
    library = Library()
    seed_library(library)
    paper = next(p for p in library.papers.values() if p.year == "2024")
    assert "Nurbekova" in paper.cite_short()
    assert paper.cite_short() != "(A., 2024)"
