#!/bin/bash

# ==============================================================================
# 🚨 CRITICAL FIX FOR GUNICORN ASYNC WORKER BLEEDING
# If you previously used `gevent` or `eventlet` workers without monkey-patching,
# database cursors will bleed across threads causing session contamination.
#
# This script explicitly uses thread workers (`gthread`) which are strictly 
# immune to async I/O memory leakage.
# ==============================================================================

NAME="efootball_project"
DJANGODIR=/path/to/efootball
USER=appuser
GROUP=appgroup
NUM_WORKERS=4
NUM_THREADS=4
DJANGO_WSGI_MODULE=efootball_project.wsgi

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source ../venv/bin/activate

# Export required environment variables
export DJANGO_SETTINGS_MODULE=$NAME.settings
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --worker-class gthread \
  --threads $NUM_THREADS \
  --user=$USER --group=$GROUP \
  --bind=127.0.0.1:8000 \
  --log-level=info \
  --max-requests=1000 \
  --max-requests-jitter=50 \
  --timeout 120
