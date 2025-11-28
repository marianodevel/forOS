from django.urls import path

from .views import CasoListView
from .views import ExpedienteSIPEDDetailView
from .views import ExpedienteSIPEDListView
from .views import ExpedienteUploadView
from .views import MovimientoExpedienteUploadView

app_name = "casos"

urlpatterns = [
    path("internos/", CasoListView.as_view(), name="caso_list"),
    path("externos/", ExpedienteSIPEDListView.as_view(), name="expediente_list"),
    path(
        "externos/<int:pk>/",
        ExpedienteSIPEDDetailView.as_view(),
        name="expediente_detail",
    ),
    # Carga de Expedientes (Lista Maestra)
    path(
        "externos/importar/",
        ExpedienteUploadView.as_view(),
        name="expediente_import",
    ),
    # Carga de Movimientos (Individual por Expediente)
    path(
        "externos/<int:pk>/movimientos/importar/",
        MovimientoExpedienteUploadView.as_view(),
        name="movimiento_expediente_import",
    ),
]
