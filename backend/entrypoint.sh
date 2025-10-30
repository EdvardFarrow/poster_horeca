#!/bin/sh



echo "--- Запускаем Миграции Базы Данных ---"
python manage.py migrate --noinput

echo "--- Собираем Статику (в S3) ---"
python manage.py collectstatic --noinput

echo "--- Запускаем Gunicorn (Веб-сервер) ---"

exec gunicorn --bind 0.0.0.0:8000 backend.wsgi:application
