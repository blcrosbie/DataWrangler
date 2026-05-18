FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/duckdb/duckdb/releases/download/v1.1.1/duckdb_cli-linux-amd64.zip -o duckdb.zip \
    && unzip duckdb.zip -d /usr/local/bin \
    && rm duckdb.zip

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "setup", "--engine", "duckdb", "--force"]
