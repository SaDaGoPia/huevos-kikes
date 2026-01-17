# Sistema SCM - Huevos Kikes

Supply Chain Management para Huevos Kikes, construido con Django. Este README refleja la **versión 2.0** e incluye notas de la **versión 1.0** para referencia.

- Demo (Render): https://huevos-kikes.onrender.com
- Admin: https://huevos-kikes.onrender.com/admin

## Resumen por versiones

### Versión 2.0 (actual)
- Seguridad: captcha en login, CSRF trusted origins parametrizable, HSTS y proxy SSL header en producción.
- Autenticación y recuperación: password reset con email HTML; SMTP con fallback a consola; login con captcha.
- UX en listados: búsqueda, paginación, filtros por fecha en ventas/compras; totales filtrados; exportación CSV/Excel/PDF.
- Dashboard: filtros rápidos (hoy/7d/30d/mes o fechas), totales ingreso/egreso/neto y gráfico 30 días (Chart.js).
- Exportables: CSV/XLSX/PDF para ventas y compras, respetando filtros.
- Datos: señales de integridad para stock/caja al borrar transacciones.
- Infra: WhiteNoise en prod, configuración dinámica de email y DB, Render-ready.

### Versión 1.0 (anterior)
- CRUD de proveedores, clientes (geolocalización), inventario, ventas y compras.
- Validación de stock en ventas y saldo de caja en compras; registro en caja; factura PDF por venta.
- Exportación básica: Excel en inventario y factura PDF de ventas.
- Dockerfile, docker-compose y configuración Render funcionales.

## Funcionalidades principales
- Login con captcha y recuperación de contraseña por email HTML.
- Proveedores: carga de RUT y Cámara de Comercio; CRUD completo.
- Clientes: geolocalización con Google Maps; captura de lat/lng.
- Inventario: tipos de huevo (A, AA, AAA) con control de stock.
- Ventas: formsets dinámicos, validación de stock, PDF de factura, caja (ingreso), export CSV/XLSX/PDF, filtros y totales.
- Compras: validación de saldo de caja, actualización de stock, caja (egreso), export CSV/XLSX/PDF, filtros y totales.
- Caja y dashboard: saldo actual, totales, últimos movimientos, filtros de rango y gráfico 30 días.
- Integridad: señales que revierten stock/caja al eliminar ventas/compras.

## Stack
- Python 3.10+
- Django 4.2.x
- PostgreSQL (producción) / SQLite (desarrollo)
- Gunicorn + WhiteNoise (estáticos)
- Docker para despliegue; Render como PaaS

## Requisitos (local)
- Windows/macOS/Linux con Python 3.10+
- Git
- PostgreSQL opcional (SQLite por defecto)

## Puesta en marcha local (PowerShell)
1) Clonar y crear entorno
```
git clone <url-del-repositorio>
cd huevos_kikes_scm
python -m venv venv
./venv/Scripts/Activate.ps1
```
2) Instalar dependencias
```
pip install -r requirements.txt
```
3) Configurar variables
```
copy .env.example .env
```
Edita .env:
```
SECRET_KEY=tu-secret-key
DEBUG=True
# DATABASE_URL=postgresql://usuario:password@localhost:5432/huevos_kikes_db
GOOGLE_MAPS_API_KEY=tu-api-key
# EMAIL_HOST_USER=...
# EMAIL_HOST_PASSWORD=...
# CSRF_TRUSTED_ORIGINS=https://tu-dominio.com
```
4) Migraciones y superusuario
```
python manage.py migrate
python manage.py createsuperuser
```
5) (Opcional) Datos iniciales de inventario
```
python manage.py shell -c "from inventario.models import TipoHuevo;\nTipoHuevo.objects.get_or_create(tipo='A', defaults={'precio_cubeta':25000,'stock_cubetas':0});\nTipoHuevo.objects.get_or_create(tipo='AA', defaults={'precio_cubeta':30000,'stock_cubetas':0});\nTipoHuevo.objects.get_or_create(tipo='AAA', defaults={'precio_cubeta':35000,'stock_cubetas':0})"
```
6) Ejecutar
```
python manage.py runserver
```

## Producción en Render (resumen)
Guía completa: ver DEPLOY_RENDER.md.

Variables Web Service (prod):
```
SECRET_KEY=<segura>
DEBUG=False
DATABASE_URL=<internal-database-url>
GOOGLE_MAPS_API_KEY=<api-key>
PYTHONVERSION=3.10
ALLOWED_HOSTS=localhost,127.0.0.1,huevos-kikes.onrender.com
CSRF_TRUSTED_ORIGINS=https://huevos-kikes.onrender.com
```
Opcionales:
```
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
RENDER_EXTERNAL_HOSTNAME=huevos-kikes.onrender.com
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@tu-dominio.com
DJANGO_SUPERUSER_PASSWORD=<pwd>
```
Arranque del contenedor (Dockerfile): migrate, crea superusuario si hay vars, collectstatic y corre Gunicorn. WhiteNoise sirve estáticos.

## Google Maps
- Clave inyectada vía context processor (settings.GOOGLE_MAPS_API_KEY).
- Restringe por HTTP referrer en GCP: https://huevos-kikes.onrender.com/*
- APIs sugeridas: Maps JavaScript API, Geocoding API.

## Integridad de datos (señales)
- transacciones/signals.py: al eliminar detalles/ventas/compras se revierte stock y caja.

## Estructura
```
huevos_kikes_scm/
├─ core/
├─ proveedores/
├─ clientes/
├─ inventario/
├─ transacciones/
├─ templates/
├─ static/
├─ staticfiles/
├─ media/
├─ huevos_kikes_scm/
├─ Dockerfile
├─ requirements.txt
└─ manage.py
```

## Troubleshooting
- 400 Bad Request en prod: define RENDER_EXTERNAL_HOSTNAME o ALLOWED_HOSTS + CSRF_TRUSTED_ORIGINS.
- Admin sin estilos / 500 static manifest: el contenedor corre collectstatic; asegúrate de que se ejecute.
- Emails en desarrollo: sin credenciales usa backend de consola; con EMAIL_HOST_USER/PASSWORD usa SMTP real.
- Captcha roto: revisa que captcha esté en INSTALLED_APPS y migrado.

## Licencia y créditos
Proyecto académico - UNIMINUTO. Parcial Tercer Corte - Sistemas de Información.
