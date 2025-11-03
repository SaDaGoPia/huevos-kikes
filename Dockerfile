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

# Ejecutar migraciones al iniciar y luego lanzar Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn huevos_kikes_scm.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
