FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt pytest.ini ./
COPY src ./src
COPY tests ./tests
COPY run.py ./

RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 1000 checker \
    && chown -R checker:checker /app

ENV PYTHONPATH=/app/src \
    QUOTE_CHECK_HOST=0.0.0.0 \
    QUOTE_CHECK_PORT=8765 \
    QUOTE_CHECK_OPEN_BROWSER=0

USER checker
EXPOSE 8765

HEALTHCHECK --interval=20s --timeout=3s --start-period=8s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/', timeout=2)"

CMD ["python", "run.py"]
