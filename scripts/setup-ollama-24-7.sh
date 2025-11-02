#!/bin/bash

# Script to set up Ollama 24/7 with Docker and integrate it into the project

set -e

if [ "$1" == "docker" ]; then
    echo "Setting up Ollama with Docker..."

    # Check if Ollama container is already running
    if docker ps --filter "name=ollama" --format "{{.Names}}" | grep -q "^ollama$"; then
        echo "Ollama container is already running."
    else
        # Run Ollama container with restart policy for 24/7 operation
        docker run -d --name ollama --restart unless-stopped -p 11434:11434 ollama/ollama
        echo "Ollama container started and set to run 24/7."
    fi

    # Wait for Ollama to be ready
    echo "Waiting for Ollama to be ready..."
    until curl -s http://localhost:11434/api/tags > /dev/null; do
        sleep 2
    done
    echo "Ollama is ready."

    if [ "$2" == "implementiraj" ]; then
        echo "Implementing Ollama: Pulling default model (llama3)..."
        docker exec ollama ollama pull llama3
        echo "Model llama3 pulled."
    fi

    if [ "$3" == "integriraj" ]; then
        echo "Integrating Ollama into the project..."

        # Update .env file if it exists
        ENV_FILE=".env"
        if [ -f "$ENV_FILE" ]; then
            # Add or update Ollama environment variables
            if ! grep -q "USE_OLLAMA" "$ENV_FILE"; then
                echo "USE_OLLAMA=true" >> "$ENV_FILE"
            else
                sed -i 's/USE_OLLAMA=.*/USE_OLLAMA=true/' "$ENV_FILE"
            fi
            if ! grep -q "OLLAMA_URL" "$ENV_FILE"; then
                echo "OLLAMA_URL=http://localhost:11434" >> "$ENV_FILE"
            else
                sed -i 's|OLLAMA_URL=.*|OLLAMA_URL=http://localhost:11434|' "$ENV_FILE"
            fi
            if ! grep -q "OLLAMA_MODEL" "$ENV_FILE"; then
                echo "OLLAMA_MODEL=llama3" >> "$ENV_FILE"
            else
                sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=llama3/' "$ENV_FILE"
            fi
            echo ".env file updated with Ollama configuration."
        else
            echo "Warning: .env file not found. Please create it and add Ollama settings manually."
        fi

        # Optionally update docker-compose.yml to include Ollama service
        COMPOSE_FILE="docker-compose.yml"
        if [ -f "$COMPOSE_FILE" ]; then
            if ! grep -q "ollama:" "$COMPOSE_FILE"; then
                echo "Adding Ollama service to docker-compose.yml..."
                cat >> "$COMPOSE_FILE" <<EOF

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    command: serve

volumes:
  ollama_data:
EOF
                echo "Ollama service added to docker-compose.yml."
            else
                echo "Ollama service already exists in docker-compose.yml."
            fi
        fi

        echo "Integration complete. Restart your backend service to use Ollama."
    fi

else
    echo "Usage: $0 docker [implementiraj] [integriraj]"
    echo "  docker: Set up Ollama using Docker"
    echo "  implementiraj: Pull the default model (llama3)"
    echo "  integriraj: Integrate Ollama into the project (.env and docker-compose.yml)"
    exit 1
fi
