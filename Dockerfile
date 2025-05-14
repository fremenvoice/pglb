FROM python:3.11-slim

# Установим нужные библиотеки для cv2 и pyzbar
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "telegram_bot.app.main"]
