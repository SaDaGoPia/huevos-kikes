from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Proveedor
from .forms import ProveedorForm


class ProveedorListView(LoginRequiredMixin, ListView):
    """Vista para listar todos los proveedores."""
    model = Proveedor
    template_name = 'proveedores/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 10
    login_url = 'core:login'

    def get_queryset(self):
        qs = super().get_queryset().order_by('-id')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(nit__icontains=q) |
                Q(telefono__icontains=q) |
                Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class ProveedorDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de un proveedor."""
    model = Proveedor
    template_name = 'proveedores/proveedor_detail.html'
    context_object_name = 'proveedor'
    login_url = 'core:login'


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo proveedor."""
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedores/proveedor_form.html'
    success_url = reverse_lazy('proveedores:list')
    login_url = 'core:login'

    def form_valid(self, form):
        """Mensaje de éxito al crear el proveedor."""
        response = super().form_valid(form)
        return response


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un proveedor existente."""
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedores/proveedor_form.html'
    success_url = reverse_lazy('proveedores:list')
    login_url = 'core:login'


class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un proveedor."""
    model = Proveedor
    template_name = 'proveedores/proveedor_confirm_delete.html'
    success_url = reverse_lazy('proveedores:list')
    login_url = 'core:login'

