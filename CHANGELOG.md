# Changelog

## 2.0 - 2026-01-17
- Seguridad: captcha en login, CSRF_TRUSTED_ORIGINS configurable, HSTS y proxy SSL header en producción.
- Autenticación: recuperación de contraseña con email HTML; fallback a consola si no hay SMTP.
- UX listados: búsqueda + paginación + filtros por fecha en ventas/compras; totales filtrados; export CSV/XLSX/PDF.
- Dashboard: filtros rápidos de rango, totales ingreso/egreso/neto, gráfico 30 días (Chart.js).
- Exportables: CSV/XLSX/PDF para ventas y compras respetando filtros.
- Integridad: señales que revierten stock/caja al eliminar ventas/compras.
- Infra: WhiteNoise en prod, configuración dinámica de email y DB.

## 1.0 - 2025-XX-XX
- CRUD de proveedores, clientes (con geolocalización), inventario, ventas y compras.
- Validación de stock en ventas y saldo de caja en compras; registro en caja; factura PDF por venta.
- Exportación básica a Excel en inventario; factura PDF por venta.
- Dockerfile, docker-compose y configuración para Render funcionales.
