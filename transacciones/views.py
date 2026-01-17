import csv
import io
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.db.models import Q, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.utils import timezone
from openpyxl import Workbook

from .models import Venta, DetalleVenta, Compra, DetalleCompra
from .forms import (
    VentaForm, DetalleVentaFormSet,
    CompraForm, DetalleCompraFormSet
)
from core.utils import registrar_transaccion_caja, get_saldo_actual


# Helpers to reuse filtering logic for list and export views
def filter_ventas_qs(request):
    qs = Venta.objects.select_related('cliente', 'usuario_vendedor').order_by('-id')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(cliente__nombre__icontains=q) |
            Q(usuario_vendedor__username__icontains=q)
        )
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        qs = qs.filter(fecha_hora__date__gte=start_date)
    if end_date:
        qs = qs.filter(fecha_hora__date__lte=end_date)
    return qs


def filter_compras_qs(request):
    qs = Compra.objects.select_related('proveedor').order_by('-id')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(proveedor__nombre__icontains=q)
        )
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        qs = qs.filter(fecha_hora__date__gte=start_date)
    if end_date:
        qs = qs.filter(fecha_hora__date__lte=end_date)
    return qs


# ==================== VENTAS ====================

class VentaListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las ventas."""
    model = Venta
    template_name = 'transacciones/venta_list.html'
    context_object_name = 'ventas'
    paginate_by = 10
    login_url = 'core:login'

    def get_queryset(self):
        return filter_ventas_qs(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        # Totals of filtered queryset (without pagination)
        filtered_qs = filter_ventas_qs(self.request)
        context['total_filtrado'] = filtered_qs.aggregate(total=Sum('total'))['total'] or 0
        params = self.request.GET.copy()
        params.pop('page', None)
        context['export_querystring'] = params.urlencode()
        return context


class VentaDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de una venta."""
    model = Venta
    template_name = 'transacciones/venta_detail.html'
    context_object_name = 'venta'
    login_url = 'core:login'


class VentaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva venta.
    Valida stock y registra la transacción en caja.
    """
    model = Venta
    form_class = VentaForm
    template_name = 'transacciones/venta_form.html'
    success_url = reverse_lazy('transacciones:ventas_list')
    login_url = 'core:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DetalleVentaFormSet(self.request.POST)
        else:
            context['formset'] = DetalleVentaFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            # Guardar la venta
            self.object = form.save(commit=False)
            self.object.usuario_vendedor = self.request.user
            self.object.save()

            # Procesar detalles
            formset.instance = self.object
            total = 0

            for detalle_form in formset:
                if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE'):
                    detalle = detalle_form.save(commit=False)
                    
                    # Validar stock disponible
                    if detalle.cantidad_cubetas > detalle.tipo_huevo.stock_cubetas:
                        messages.error(
                            self.request,
                            f"Stock insuficiente para {detalle.tipo_huevo.tipo}. "
                            f"Disponible: {detalle.tipo_huevo.stock_cubetas} cubetas."
                        )
                        transaction.set_rollback(True)
                        return self.form_invalid(form)

                    # Restar del stock
                    detalle.tipo_huevo.stock_cubetas -= detalle.cantidad_cubetas
                    detalle.tipo_huevo.save()

                    # Guardar detalle
                    detalle.venta = self.object
                    detalle.save()

                    # Acumular total
                    total += detalle.subtotal

            # Actualizar total de la venta
            self.object.total = total
            self.object.save()

            # Registrar ingreso en caja
            registrar_transaccion_caja(
                monto=total,
                tipo='ingreso',
                venta_id=self.object.id,
                descripcion=f"Venta #{self.object.id} - {self.object.cliente.nombre}"
            )

            messages.success(self.request, f"Venta #{self.object.id} creada exitosamente.")
            
            # Redirigir a la página de generación de PDF
            return redirect('transacciones:venta_pdf', pk=self.object.id)


class VentaUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar una venta existente."""
    model = Venta
    form_class = VentaForm
    template_name = 'transacciones/venta_form.html'
    success_url = reverse_lazy('transacciones:ventas_list')
    login_url = 'core:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DetalleVentaFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = DetalleVentaFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Recalcular total
            total = sum(detalle.subtotal for detalle in self.object.detalles.all())
            self.object.total = total
            self.object.save()

            messages.success(self.request, f"Venta #{self.object.id} actualizada exitosamente.")
            return redirect(self.success_url)


# ==================== COMPRAS ====================

class CompraListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las compras."""
    model = Compra
    template_name = 'transacciones/compra_list.html'
    context_object_name = 'compras'
    paginate_by = 10
    login_url = 'core:login'

    def get_queryset(self):
        return filter_compras_qs(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        filtered_qs = filter_compras_qs(self.request)
        context['total_filtrado'] = filtered_qs.aggregate(total=Sum('total'))['total'] or 0
        params = self.request.GET.copy()
        params.pop('page', None)
        context['export_querystring'] = params.urlencode()
        return context


class CompraDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de una compra."""
    model = Compra
    template_name = 'transacciones/compra_detail.html'
    context_object_name = 'compra'
    login_url = 'core:login'


class CompraCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva compra.
    Valida saldo en caja y registra la transacción.
    """
    model = Compra
    form_class = CompraForm
    template_name = 'transacciones/compra_form.html'
    success_url = reverse_lazy('transacciones:compras_list')
    login_url = 'core:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DetalleCompraFormSet(self.request.POST)
        else:
            context['formset'] = DetalleCompraFormSet()
        context['saldo_actual'] = get_saldo_actual()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            return self.form_invalid(form)

        # Calcular total de la compra
        total = 0
        detalles_data = []
        for detalle_form in formset:
            if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE'):
                cantidad = detalle_form.cleaned_data['cantidad_cubetas']
                precio = detalle_form.cleaned_data['precio_unitario_cubeta']
                total += cantidad * precio
                detalles_data.append(detalle_form.cleaned_data)

        # Validar saldo en caja
        saldo_actual = get_saldo_actual()
        if total > saldo_actual:
            messages.error(
                self.request,
                f"Saldo en caja insuficiente. Saldo actual: ${saldo_actual:.2f}, "
                f"Total de compra: ${total:.2f}"
            )
            return self.form_invalid(form)

        with transaction.atomic():
            # Guardar la compra
            self.object = form.save(commit=False)
            self.object.total = total
            self.object.save()

            # Procesar detalles
            for detalle_data in detalles_data:
                detalle = DetalleCompra(
                    compra=self.object,
                    tipo_huevo=detalle_data['tipo_huevo'],
                    cantidad_cubetas=detalle_data['cantidad_cubetas'],
                    precio_unitario_cubeta=detalle_data['precio_unitario_cubeta']
                )
                
                # Aumentar el stock
                detalle.tipo_huevo.stock_cubetas += detalle.cantidad_cubetas
                detalle.tipo_huevo.save()
                
                detalle.save()

            # Registrar egreso en caja
            registrar_transaccion_caja(
                monto=total,
                tipo='egreso',
                compra_id=self.object.id,
                descripcion=f"Compra #{self.object.id} - {self.object.proveedor.nombre}"
            )

            messages.success(self.request, f"Compra #{self.object.id} creada exitosamente.")
            return redirect(self.success_url)


class CompraUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar una compra existente."""
    model = Compra
    form_class = CompraForm
    template_name = 'transacciones/compra_form.html'
    success_url = reverse_lazy('transacciones:compras_list')
    login_url = 'core:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DetalleCompraFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = DetalleCompraFormSet(instance=self.object)
        context['saldo_actual'] = get_saldo_actual()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Recalcular total
            total = sum(detalle.subtotal for detalle in self.object.detalles.all())
            self.object.total = total
            self.object.save()

            messages.success(self.request, f"Compra #{self.object.id} actualizada exitosamente.")
            return redirect(self.success_url)


# ==================== GENERACIÓN DE PDF ====================

def generar_factura_pdf(request, pk):
    """
    Genera una factura en PDF para una venta específica.
    """
    venta = get_object_or_404(Venta, pk=pk)
    
    # Renderizar el template HTML
    html_string = render_to_string('transacciones/factura_pdf.html', {
        'venta': venta,
        'detalles': venta.detalles.all(),
    })

    # Generar PDF con WeasyPrint
    html = HTML(string=html_string)
    result = html.write_pdf()

    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=factura_venta_{venta.id}.pdf'
    response.write(result)

    return response


# ================ EXPORTACIONES CSV =================

class VentaCSVExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_ventas_qs(request)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=ventas.csv'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Cliente', 'Vendedor', 'Fecha', 'Total'])
        for venta in qs:
            fecha_local = timezone.localtime(venta.fecha_hora)
            writer.writerow([
                venta.id,
                venta.cliente.nombre,
                venta.usuario_vendedor.username,
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                f'{venta.total:.2f}',
            ])

        return response


class CompraCSVExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_compras_qs(request)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=compras.csv'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Proveedor', 'Fecha', 'Medio de Pago', 'Total'])
        for compra in qs:
            fecha_local = timezone.localtime(compra.fecha_hora)
            writer.writerow([
                compra.id,
                compra.proveedor.nombre,
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                compra.get_medio_pago_display(),
                f'{compra.total:.2f}',
            ])

        return response


class VentaXLSXExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_ventas_qs(request)

        wb = Workbook()
        ws = wb.active
        ws.title = 'Ventas'
        ws.append(['ID', 'Cliente', 'Vendedor', 'Fecha', 'Total'])

        for venta in qs:
            fecha_local = timezone.localtime(venta.fecha_hora)
            ws.append([
                venta.id,
                venta.cliente.nombre,
                venta.usuario_vendedor.username,
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                float(venta.total),
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=ventas.xlsx'
        return response


class CompraXLSXExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_compras_qs(request)

        wb = Workbook()
        ws = wb.active
        ws.title = 'Compras'
        ws.append(['ID', 'Proveedor', 'Fecha', 'Medio de Pago', 'Total'])

        for compra in qs:
            fecha_local = timezone.localtime(compra.fecha_hora)
            ws.append([
                compra.id,
                compra.proveedor.nombre,
                fecha_local.strftime('%Y-%m-%d %H:%M'),
                compra.get_medio_pago_display(),
                float(compra.total),
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=compras.xlsx'
        return response


class VentaPDFExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_ventas_qs(request)
        total_filtrado = qs.aggregate(total=Sum('total'))['total'] or 0

        html_string = render_to_string('transacciones/venta_list_pdf.html', {
            'ventas': qs,
            'total_filtrado': total_filtrado,
            'generated_at': timezone.localtime(),
        })

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=ventas.pdf'
        return response


class CompraPDFExportView(LoginRequiredMixin, View):
    login_url = 'core:login'

    def get(self, request, *args, **kwargs):
        qs = filter_compras_qs(request)
        total_filtrado = qs.aggregate(total=Sum('total'))['total'] or 0

        html_string = render_to_string('transacciones/compra_list_pdf.html', {
            'compras': qs,
            'total_filtrado': total_filtrado,
            'generated_at': timezone.localtime(),
        })

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=compras.pdf'
        return response

