from django.urls import path

from .views import CasoDetailModalView
from .views import CasoListView
from .views import ExpedienteSIPEDDetailView
from .views import ExpedienteSIPEDListView
from .views import ExpedienteUploadView
from .views import MatrizTareasView
from .views import MovimientoExpedienteUploadView
from .views import TareaCreateView
from .views import TareaUpdateView

app_name = "casos"

urlpatterns = [
    path("internos/", CasoListView.as_view(), name="caso_list"),
    path("externos/", ExpedienteSIPEDListView.as_view(), name="expediente_list"),
    path(
        "externos/<int:pk>/",
        ExpedienteSIPEDDetailView.as_view(),
        name="expediente_detail",
    ),
    path(
        "externos/importar/",
        ExpedienteUploadView.as_view(),
        name="expediente_import",
    ),
    path(
        "externos/<int:pk>/movimientos/importar/",
        MovimientoExpedienteUploadView.as_view(),
        name="movimiento_expediente_import",
    ),
    # Gestión de Tareas (Matriz)
    path("matriz/", MatrizTareasView.as_view(), name="matriz"),
    path("tarea/<int:pk>/editar/", TareaUpdateView.as_view(), name="tarea_editar"),
    path(
        "caso/<int:caso_id>/nueva-tarea/",
        TareaCreateView.as_view(),
        name="tarea_crear",
    ),
    # Detalle del Caso (Modal)
    path(
        "caso/<int:pk>/detalle/",
        CasoDetailModalView.as_view(),
        name="caso_detalle",
    ),
]
