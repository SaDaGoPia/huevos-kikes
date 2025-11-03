# Sistema SCM - Huevos Kikes 🥚

Sistema de gestión de cadena de suministro (Supply Chain Management) para Huevos Kikes, desarrollado con Django.

- Demo (Render): https://huevos-kikes.onrender.com
- Admin: https://huevos-kikes.onrender.com/admin

## ✨ Funcionalidades

- Proveedores: documentos (RUT, Cámara de Comercio) y CRUD
- Clientes: geolocalización con Google Maps y captura de coordenadas
- Inventario: tipos de huevo (A, AA, AAA) y control de stock
- Ventas: formsets dinámicos, validación de stock, PDF de factura, registro en caja
- Compras: validación de caja, actualización de stock, registro en caja
- Caja: saldo actual, ingresos/egresos, dashboard
- Integridad de datos: señales que restauran stock y ajustan caja al borrar/editar ventas y compras

## 🚀 Stack

- Python 3.10+
- Django 4.2.x
- PostgreSQL (producción) / SQLite (desarrollo)
- Gunicorn + WhiteNoise (estáticos)
- Docker (construcción y despliegue)
- Render (PaaS)

## 🧱 Requisitos (local)

- Windows/macOS/Linux con Python 3.10+
- Git
- PostgreSQL opcional (SQLite por defecto)

## 🛠️ Puesta en marcha local

1) Clonar y crear entorno virtual (Windows PowerShell)
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

3) Configurar variables de entorno
```
copy .env.example .env
```
Edita .env:
```
SECRET_KEY=tu-secret-key
DEBUG=True
# DATABASE_URL=postgresql://usuario:password@localhost:5432/huevos_kikes_db
GOOGLE_MAPS_API_KEY=tu-api-key
```

4) Migraciones y usuario admin
```
python manage.py migrate
python manage.py createsuperuser
```

5) (Opcional) Datos iniciales
```
python manage.py shell -c "from inventario.models import TipoHuevo;\nTipoHuevo.objects.get_or_create(tipo='A', defaults={'precio_cubeta':25000,'stock_cubetas':0});\nTipoHuevo.objects.get_or_create(tipo='AA', defaults={'precio_cubeta':30000,'stock_cubetas':0});\nTipoHuevo.objects.get_or_create(tipo='AAA', defaults={'precio_cubeta':35000,'stock_cubetas':0})"
```

6) Ejecutar
```
python manage.py runserver
```

## 🐳 Producción en Render (resumen)

Guía completa: ver `DEPLOY_RENDER.md`. Resumen de variables:

Obligatorias (Web Service):
```
SECRET_KEY=<segura>
DEBUG=False
DATABASE_URL=<internal-database-url>
PYTHONVERSION=3.10
GOOGLE_MAPS_API_KEY=<tu-api-key>
```
Hosts:
```
# Añade uno de los dos (o ambos)
RENDER_EXTERNAL_HOSTNAME=huevos-kikes.onrender.com
ALLOWED_HOSTS=localhost,127.0.0.1,huevos-kikes.onrender.com
```
Admin automático (opcional):
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@tu-dominio.com
DJANGO_SUPERUSER_PASSWORD=<contraseña>
```

Qué hace el contenedor al arrancar (Dockerfile):
- Ejecuta `migrate` automáticamente
- Crea superusuario si están las variables `DJANGO_SUPERUSER_*`
- Ejecuta `collectstatic --noinput`
- Arranca Gunicorn

Estáticos en producción:
- WhiteNoise habilitado (middleware + CompressedManifest)

## 🗺️ Google Maps

- La clave se inyecta a templates vía context processor (`settings.GOOGLE_MAPS_API_KEY`)
- En Google Cloud Console, restringe la clave por HTTP referrer a tu dominio de Render: `https://huevos-kikes.onrender.com/*`
- APIs sugeridas: Maps JavaScript API, Geocoding API

## 🧩 Integridad de datos (señales)

Archivo: `transacciones/signals.py`
- Al eliminar DetalleVenta → restaura stock
- Al eliminar Venta → elimina ingreso en caja
- Al eliminar DetalleCompra → descuenta stock agregado
- Al eliminar Compra → elimina egreso en caja

Registradas en `transacciones/apps.py` (ready).

## 📁 Estructura

```
huevos_kikes_scm/
├─ core/                # Auth, dashboard, caja
├─ proveedores/
├─ clientes/
├─ inventario/
├─ transacciones/
├─ templates/
├─ static/              # Dev
├─ staticfiles/         # Prod (collectstatic)
├─ media/
├─ huevos_kikes_scm/    # settings/urls/wsgi
├─ Dockerfile
├─ requirements.txt
└─ manage.py
```

## 🧰 Troubleshooting

- 400 Bad Request en producción: define `RENDER_EXTERNAL_HOSTNAME` o `ALLOWED_HOSTS` con tu dominio.
- Admin sin estilos / 500 Missing staticfiles manifest: ya está WhiteNoise; el contenedor corre `collectstatic` en arranque.
- Error en ventas por PDF: usar URL name `transacciones:venta_pdf` (corregido en templates).

## 📄 Licencia y créditos

Proyecto académico - UNIMINUTO

—

Parcial Tercer Corte - Sistemas de Información

