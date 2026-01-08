FROM mcr.microsoft.com/devcontainers/python:3.11
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY . /app
CMD ["python", "main.py", "autoscout24_complete"]
