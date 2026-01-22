FROM python:3.11-slim

# Install system dependencies for WeasyPrint and Postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libxcb1 \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Run as non-root user
RUN useradd -m app
# Ensure media and static directories exist and are writable
RUN mkdir -p /app/media /app/staticfiles && chown -R app:app /app/media /app/staticfiles

USER app

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "prosnabdb.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
