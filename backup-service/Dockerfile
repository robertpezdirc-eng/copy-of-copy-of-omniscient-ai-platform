FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:slim

# Install git, curl, and Flask for the HTTP server
RUN apt-get update && apt-get install -y git curl python3-flask && rm -rf /var/lib/apt/lists/*

ENV PORT=8080
WORKDIR /app

COPY run_backup.sh /app/run_backup.sh
COPY app.py /app/app.py

RUN chmod +x /app/run_backup.sh

EXPOSE 8080
CMD ["python3", "app.py"]
