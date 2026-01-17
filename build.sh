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
echo "Build completed successfully!"
echo "================================================"
