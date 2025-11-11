from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Caso
from .models import ExpedienteSiped


class CasoListView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar la lista de todos los casos internos.
    """

    model = Caso
    template_name = "casos/caso_list.html"
    context_object_name = "casos"
    paginate_by = 25


class ExpedienteSIPEDListView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar la lista de todos los expedientes de SIPED.
    """

    model = ExpedienteSiped
    template_name = "casos/expediente_siped_list.html"
    context_object_name = "expedientes"
    paginate_by = 25
