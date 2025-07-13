FROM python:3.10-slim

# Install system dependencies for Chrome & Selenium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    curl \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for headless Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]