from quote_check.library import Library, seed_library
from quote_check.writer import chat, continue_writing, outline


def test_chat_answers_from_library_and_marks_quotes():
    library = Library()
    seed_library(library)
    result = chat(library, "почему нельзя закрывать карточку без страницы")
    assert "внешних" in result["text"] or "статус" in result["text"].casefold() or result["hits"]
    assert result["hits"]
    assert result["hits"][0]["status"] in {"cited", "unchecked"}


def test_chat_does_not_invent_missing_topic():
    library = Library()
    seed_library(library)
    result = chat(library, "квантовый компьютер на Марсе и рецепт борща")
    assert result["hits"] == [] or "нет" in result["text"].casefold()


def test_continue_and_outline_use_sources():
    library = Library()
    seed_library(library)
    cont = continue_writing(library, "Карточка статьи не должна врать про страницу цитаты.")
    plan = outline(library, "цитата страница карточка")
    assert cont["hits"]
    assert "План" in plan["text"]
    assert plan["bibliography"]
