#!/bin/bash
set -e
gunicorn app:app --bind 0.0.0.0:${PORT:-8000} &
exec python3 bot.py
