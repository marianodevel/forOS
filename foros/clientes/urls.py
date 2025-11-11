from django.urls import path

from .views import ClienteListView

app_name = "clientes"  # Para usar {% url 'clientes:list' %}

urlpatterns = [
    path("", ClienteListView.as_view(), name="list"),
    # Aquí irán las vistas de detalle, creación, etc.
]
