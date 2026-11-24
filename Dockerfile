FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    LAB04_HOME=simulator

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends ngspice \
    && rm -rf /var/lib/apt/lists/* \
    && ngspice --version

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 'gunicorn>=23,<24'

COPY bjt/ bjt/
COPY web/ web/
RUN useradd --system --no-create-home app
USER app

EXPOSE 10000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 30 web.app:app"]
