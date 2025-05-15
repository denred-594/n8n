FROM python:3.9-slim

# Installiere Abhängigkeiten für WeasyPrint und Pyppeteer
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/

# Umgebungsvariable für Pyppeteer
ENV PYPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

CMD ["python", "app.py"]