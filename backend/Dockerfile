FROM python:3.11-slim

# I am setting these environment variables to ensure Python output is sent 
# straight to the logs and to prevent .pyc files from being created.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# I've included the necessary libraries for building the PostgreSQL adapter.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# I am copying the requirements first to take advantage of Docker's layer caching.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
