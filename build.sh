#!/bin/bash
set -e

echo "================================================"
echo "Running Database Migrations..."
echo "================================================"
python manage.py migrate --noinput

echo "================================================"
echo "Collecting Static Files..."
echo "================================================"
python manage.py collectstatic --noinput

echo "================================================"
echo "Creating superuser if variables are present..."
echo "================================================"
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
	python manage.py createsuperuser --noinput 2>/dev/null || echo "Superuser already exists"
else
	echo "Skipping superuser creation (missing DJANGO_SUPERUSER_* env vars)"
fi

echo "================================================"
echo "Build completed successfully!"
echo "================================================"
