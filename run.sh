#!/usr/bin/env bash

# Start Celery worker in the background (using solo pool for low memory)
echo "Starting Celery worker..."
celery -A efootball_project worker --loglevel=info --concurrency=1 --pool=solo &

# Start Gunicorn (Using strictly gthread workers to prevent session bleeding)
echo "Starting Gunicorn..."
gunicorn efootball_project.wsgi:application \
    --worker-class gthread \
    --threads 4 \
    --workers 2 \
    --bind 0.0.0.0:$PORT

