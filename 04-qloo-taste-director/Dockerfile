FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.lock \
    && useradd --uid 10001 --create-home taste \
    && mkdir /data && chown taste:taste /data
COPY --chown=taste:taste taste ./taste
COPY --chown=taste:taste static ./static
COPY --chown=taste:taste launcher.py LICENSE ./
USER taste
ENV PORT=8714 TASTE_DATA_DIR=/data
EXPOSE 8714
VOLUME ["/data"]
CMD ["python", "launcher.py", "--host", "0.0.0.0", "--no-browser"]
