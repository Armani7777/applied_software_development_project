"""Короткий запуск из консоли: файл страницы, номер, цитата."""

import sys

from quote_check.check import field_status


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        from quote_check.server import serve

        serve()
        return 0
    if len(args) != 3:
        print("usage: python -m quote_check <page.txt> <page_number> <quote>")
        return 2
    path, page_raw, quote = args
    try:
        page = int(page_raw)
    except ValueError:
        print("page number must be an integer")
        return 2
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    result = field_status(text, quote, page)
    print(f"page={result['page']} status={result['status']}")
    return 0 if result["status"] == "cited" else 1


if __name__ == "__main__":
    raise SystemExit(main())
