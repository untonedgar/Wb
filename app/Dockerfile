FROM python:3.11-slim

WORKDIR /usr/src/app


RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libxss1 \
    libxtst6 \
    libx11-xcb1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    wget \
    curl \
    unzip \
    netcat-openbsd \
    gettext\
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.prod.sh
RUN chmod +x /usr/src/app/entrypoint.prod.sh

ENTRYPOINT [ "./entrypoint.prod.sh" ]