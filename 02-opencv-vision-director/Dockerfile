FROM python:3.12.14-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VISION_EXECUTION_ENV=aws-ec2 VISION_DATA_DIR=/app/runtime
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.lock && useradd --uid 10001 --create-home app
COPY vision ./vision
COPY static ./static
COPY tools ./tools
COPY examples ./examples
RUN mkdir -p /app/runtime && chown -R app:app /app/runtime
USER 10001:10001
EXPOSE 8712
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8712/api/health', timeout=3)"
CMD ["python","-m","uvicorn","vision.server:app","--host","0.0.0.0","--port","8712","--workers","1"]
