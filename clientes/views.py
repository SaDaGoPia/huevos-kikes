from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cliente
from .forms import ClienteForm


class ClienteListView(LoginRequiredMixin, ListView):
    """Vista para listar todos los clientes."""
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10
    login_url = 'core:login'

    def get_queryset(self):
        qs = super().get_queryset().order_by('-id')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(cedula_nit__icontains=q) |
                Q(telefono__icontains=q) |
                Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class ClienteDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de un cliente."""
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'
    login_url = 'core:login'


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo cliente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:list')
    login_url = 'core:login'


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un cliente existente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:list')
    login_url = 'core:login'


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un cliente."""
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:list')
    login_url = 'core:login'

