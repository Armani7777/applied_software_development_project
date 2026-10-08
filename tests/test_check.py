from quote_check.check import collapse, field_status, match_span, quote_found


PAGE = (
    "В работе сравнивают сжатие JPEG и точность детекции.\n"
    "Авторы пишут, что метрики PSNR и SSIM плохо совпадают с mAP.\n"
    "Проверка шла на выборке COCO val2017."
)


def test_quote_survives_line_breaks():
    quote = "метрики PSNR и SSIM плохо совпадают с mAP"
    assert quote_found(PAGE, quote)


def test_missing_quote_is_not_a_hit():
    assert quote_found(PAGE, "модель обучали с нуля на ImageNet") is False


def test_empty_quote_does_not_count_as_found():
    assert quote_found(PAGE, "   ") is False
    status = field_status(PAGE, "", 4)
    assert status["status"] == "empty"
    assert status["found"] is False
    assert status["page"] == 4


def test_wrong_page_text_stays_unchecked():
    status = field_status("Совсем другой абзац про погоду.", "COCO val2017", 2)
    assert status == {"page": 2, "found": False, "status": "unchecked"}


def test_case_and_extra_spaces_are_ignored():
    quote = "  Метрики   psnr и ssim\nплохо   совпадают с MAP "
    assert quote_found(PAGE, quote)


def test_match_span_points_at_the_phrase():
    quote = "метрики   PSNR и SSIM плохо совпадают с mAP"
    span = match_span(PAGE, quote)
    assert span is not None
    start, end = span
    assert collapse(PAGE[start:end]) == collapse(quote)


def test_match_span_is_missing_for_a_foreign_phrase():
    assert match_span(PAGE, "модель обучали с нуля на ImageNet") is None
