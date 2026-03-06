FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    gcc \
    git \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# pip + setuptools rendbetétele
RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "index.py"]