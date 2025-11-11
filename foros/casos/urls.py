from django.urls import path

from .views import CasoListView
from .views import ExpedienteSIPEDListView

app_name = "casos"

urlpatterns = [
    path("internos/", CasoListView.as_view(), name="caso_list"),
    path("externos/", ExpedienteSIPEDListView.as_view(), name="expediente_list"),
    # Aquí irán las vistas de detalle, etc.
]
