# Dockerfile para Huevos Kikes SCM
# Optimizado para producción con Render

FROM python:3.10-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y WeasyPrint
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput || true

# Exponer el puerto 8000
EXPOSE 8000

# Script de inicio para ejecutar migraciones y luego Gunicorn
RUN echo '#!/bin/bash\nset -e\n\necho "Running migrations..."\npython manage.py migrate --noinput\n\necho "Collecting static files..."\npython manage.py collectstatic --noinput\n\necho "Creating superuser if needed..."\nif [ -z "$DJANGO_SUPERUSER_USERNAME" ]; then\n  echo "DJANGO_SUPERUSER_USERNAME not set, skipping superuser creation"\nelse\n  python manage.py createsuperuser --noinput 2>/dev/null || echo "Superuser already exists"\nfi\n\necho "Starting Gunicorn..."\ngunicorn huevos_kikes_scm.wsgi:application --bind 0.0.0.0:8000 --workers 3' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]