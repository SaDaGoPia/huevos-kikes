from datetime import date, timedelta

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate
from .models import TransaccionCaja
from .utils import get_saldo_actual
from .forms import LoginFormWithCaptcha


class CustomLoginView(LoginView):
    """Vista personalizada para el login con captcha."""
    template_name = 'core/login.html'
    form_class = LoginFormWithCaptcha
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Vista personalizada para el logout."""
    next_page = 'core:login'


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista del Dashboard principal que muestra:
    - Saldo actual en caja
    - Últimas 10 transacciones de ingreso
    - Últimas 10 transacciones de egreso
    """
    template_name = 'core/dashboard.html'
    login_url = 'core:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener rango de fechas (por GET: start_date/end_date o range= today/7d/30d/month)
        start_date, end_date, rango_label = self._get_date_range()

        # Obtener saldo actual (independiente del filtro)
        context['saldo_actual'] = get_saldo_actual()

        # Query base filtrada por fechas si aplica
        base_qs = TransaccionCaja.objects.all()
        if start_date:
            base_qs = base_qs.filter(fecha_hora__date__gte=start_date)
        if end_date:
            base_qs = base_qs.filter(fecha_hora__date__lte=end_date)

        # Últimas 10 transacciones por tipo, respetando filtro
        context['ingresos_recientes'] = base_qs.filter(tipo='ingreso')[:10]
        context['egresos_recientes'] = base_qs.filter(tipo='egreso')[:10]

        # Totales
        context['total_ingresos'] = base_qs.filter(tipo='ingreso').aggregate(total=Sum('monto'))['total'] or 0
        context['total_egresos'] = base_qs.filter(tipo='egreso').aggregate(total=Sum('monto'))['total'] or 0
        context['total_neto'] = context['total_ingresos'] - context['total_egresos']

        # Serie para gráfico (últimos 30 días)
        chart_start = timezone.localdate() - timedelta(days=29)
        chart_qs = TransaccionCaja.objects.filter(fecha_hora__date__gte=chart_start)
        chart_ingresos = chart_qs.filter(tipo='ingreso').annotate(d=TruncDate('fecha_hora')).values('d').annotate(total=Sum('monto')).order_by('d')
        chart_egresos = chart_qs.filter(tipo='egreso').annotate(d=TruncDate('fecha_hora')).values('d').annotate(total=Sum('monto')).order_by('d')

        def series_to_map(qs):
            return {item['d'].isoformat(): float(item['total']) for item in qs}

        ingresos_map = series_to_map(chart_ingresos)
        egresos_map = series_to_map(chart_egresos)

        labels = [ (chart_start + timedelta(days=i)).isoformat() for i in range(30) ]
        context['chart_labels'] = labels
        context['chart_ingresos'] = [ingresos_map.get(day, 0) for day in labels]
        context['chart_egresos'] = [egresos_map.get(day, 0) for day in labels]

        # Filtros en contexto
        context['start_date'] = start_date.isoformat() if start_date else ''
        context['end_date'] = end_date.isoformat() if end_date else ''
        context['rango_label'] = rango_label
        context['rango'] = self.request.GET.get('range', '')

        return context

    def _get_date_range(self):
        """Devuelve (start_date, end_date, label) según GET params."""
        today = timezone.localdate()
        start_date_param = self.request.GET.get('start_date')
        end_date_param = self.request.GET.get('end_date')
        range_key = self.request.GET.get('range')

        start_date = None
        end_date = None
        label = 'Todo'

        # Si hay fechas explícitas, priorizarlas
        if start_date_param:
            try:
                start_date = date.fromisoformat(start_date_param)
            except ValueError:
                start_date = None
        if end_date_param:
            try:
                end_date = date.fromisoformat(end_date_param)
            except ValueError:
                end_date = None

        # Si no hay fechas manuales, usar rango rápido
        if not start_date and not end_date and range_key:
            if range_key == 'today':
                start_date = today
                end_date = today
                label = 'Hoy'
            elif range_key == '7d':
                start_date = today - timedelta(days=6)
                end_date = today
                label = 'Últimos 7 días'
            elif range_key == '30d':
                start_date = today - timedelta(days=29)
                end_date = today
                label = 'Últimos 30 días'
            elif range_key == 'month':
                start_date = today.replace(day=1)
                end_date = today
                label = 'Mes en curso'

        # Etiqueta cuando hay fechas manuales
        if start_date_param or end_date_param:
            label = 'Rango personalizado'

        return start_date, end_date, label


class CustomPasswordResetView(PasswordResetView):
    """
    Vista personalizada para recuperación de contraseña que envía emails en formato HTML.
    Sobrescribe el método send_mail para usar EmailMultiAlternatives.
    """
    template_name = 'core/password_reset.html'
    email_template_name = 'core/password_reset_email.html'
    subject_template_name = 'core/password_reset_subject.txt'
    success_url = '/password-reset/done/'
    html_email_template_name = 'core/password_reset_email.html'
    
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Envía el email de recuperación de contraseña en formato HTML.
        """
        # Renderizar el asunto
        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())  # Eliminar saltos de línea
        
        # Renderizar el cuerpo HTML
        html_content = render_to_string(html_email_template_name or email_template_name, context)
        
        # Crear el mensaje con EmailMultiAlternatives para HTML
        email_message = EmailMultiAlternatives(
            subject=subject,
            body='',  # Cuerpo vacío para texto plano
            from_email=from_email,
            to=[to_email]
        )
        
        # Adjuntar la versión HTML
        email_message.attach_alternative(html_content, "text/html")
        
        # Enviar el email
        email_message.send()

