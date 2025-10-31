FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:slim

# Install git and curl for cloning and health checks
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

ENV PORT=8080
WORKDIR /app

COPY run_backup.sh /app/run_backup.sh
COPY app.py /app/app.py

RUN chmod +x /app/run_backup.sh \
    && pip install --no-cache-dir Flask

EXPOSE 8080
CMD ["python", "app.py"]
