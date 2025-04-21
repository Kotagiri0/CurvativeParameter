FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости для mysqlclient и mysql-client
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    mariadb-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY . .

# Делаем entrypoint.sh исполняемым
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]