from quote_check.server import evaluate

PAGE = (
    "В работе сравнивают сжатие JPEG и точность детекции.\n"
    "Авторы пишут, что метрики PSNR и SSIM плохо совпадают с mAP.\n"
    "Проверка шла на выборке COCO val2017."
)


def test_page_returns_cited_and_a_span():
    status, body = evaluate({
        "page_text": PAGE,
        "quote": "метрики   PSNR и SSIM плохо совпадают с mAP",
        "page": "4",
    })
    assert status == 200
    assert body["status"] == "cited"
    assert body["start"] is not None
    assert body["end"] > body["start"]


def test_blank_quote_is_empty_without_a_span():
    status, body = evaluate({"page_text": PAGE, "quote": "   ", "page": 4})
    assert status == 200
    assert body["status"] == "empty"
    assert body["start"] is None


def test_page_number_must_be_an_integer():
    status, body = evaluate({"page_text": PAGE, "quote": "COCO", "page": "четыре"})
    assert status == 400
    assert "целым" in body["error"]
