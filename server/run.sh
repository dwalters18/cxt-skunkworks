#!/bin/bash

# Check for arguments to run locally or with Docker
if [ "$1" == "docker" ]; then
  echo "Running in Docker..."
  docker build -t cxt-skunkworks-server .
  docker run --env-file .env -p 8000:8000 cxt-skunkworks-server
else
  echo "Running locally..."

  # Load environment variables from .env file if it exists
  if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "Environment variables loaded from .env"
  else
    echo ".env file not found. Using system environment variables."
  fi

  # Activate the Conda environment
  if [ -d "$HOME/miniconda3" ]; then
    source "$HOME/miniconda3/bin/activate" cxt-skunkworks-server
  elif [ -d "$HOME/anaconda3" ]; then
    source "$HOME/anaconda3/bin/activate" cxt-skunkworks-server
  else
    echo "Conda not found. Make sure it's installed and available in your PATH."
    exit 1
  fi

  # Start the FastAPI application with Uvicorn
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
fi
