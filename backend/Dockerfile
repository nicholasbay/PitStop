FROM python:3.12-bookworm
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# netcat: Database connection checks in entrypoint script
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

COPY . .
EXPOSE 8000

RUN mkdir -p logs data && \
    chmod +x ./entrypoint.sh && \
    useradd appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["sh", "./entrypoint.sh"]
