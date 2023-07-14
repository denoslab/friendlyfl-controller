#!/bin/sh
poetry run python3 manage.py makemigrations --no-input
poetry run python3 manage.py migrate --no-input
poetry run python3 manage.py runserver 0.0.0.0:8000
