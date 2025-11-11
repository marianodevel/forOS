from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Cliente


class ClienteListView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar la lista de todos los clientes.
    """

    model = Cliente
    # Django buscará automáticamente: /templates/clientes/cliente_list.html
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 25  # Opcional: paginación
