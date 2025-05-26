# Dockerfile
FROM python:3.11-slim

# 1) Set workdir, envs
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2) Install system deps (if you need build-tools)
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    libgl1 \
    libglib2.0-0 \
    wget && \
    rm -rf /var/lib/apt/lists/*

# 3) Copy & install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4) Copy the rest of your code
COPY . .

# 5) Expose and launch
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]