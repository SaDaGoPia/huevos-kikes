"""
URLs para la app de transacciones (ventas y compras).
"""
from django.urls import path
from .views import (
    VentaListView, VentaDetailView, VentaCreateView, VentaUpdateView,
    CompraListView, CompraDetailView, CompraCreateView, CompraUpdateView,
    VentaCSVExportView, CompraCSVExportView,
    VentaXLSXExportView, CompraXLSXExportView,
    VentaPDFExportView, CompraPDFExportView,
    generar_factura_pdf
)

app_name = 'transacciones'

urlpatterns = [
    # Ventas
    path('ventas/', VentaListView.as_view(), name='ventas_list'),
    path('ventas/export/csv/', VentaCSVExportView.as_view(), name='ventas_export_csv'),
    path('ventas/export/xlsx/', VentaXLSXExportView.as_view(), name='ventas_export_xlsx'),
    path('ventas/export/pdf/', VentaPDFExportView.as_view(), name='ventas_export_pdf'),
    path('ventas/<int:pk>/', VentaDetailView.as_view(), name='venta_detail'),
    path('ventas/crear/', VentaCreateView.as_view(), name='venta_create'),
    path('ventas/<int:pk>/editar/', VentaUpdateView.as_view(), name='venta_update'),
    path('ventas/<int:pk>/pdf/', generar_factura_pdf, name='venta_pdf'),
    
    # Compras
    path('compras/', CompraListView.as_view(), name='compras_list'),
    path('compras/export/csv/', CompraCSVExportView.as_view(), name='compras_export_csv'),
    path('compras/export/xlsx/', CompraXLSXExportView.as_view(), name='compras_export_xlsx'),
    path('compras/export/pdf/', CompraPDFExportView.as_view(), name='compras_export_pdf'),
    path('compras/<int:pk>/', CompraDetailView.as_view(), name='compra_detail'),
    path('compras/crear/', CompraCreateView.as_view(), name='compra_create'),
    path('compras/<int:pk>/editar/', CompraUpdateView.as_view(), name='compra_update'),
]
