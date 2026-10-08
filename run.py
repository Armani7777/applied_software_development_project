"""Открывает страницу проверки в браузере. Из папки репозитория: python run.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from quote_check.server import serve

if __name__ == "__main__":
    serve()
