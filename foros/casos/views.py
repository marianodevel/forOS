import contextlib
import csv
import io
import logging
import re
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .forms import ExpedienteUploadForm
from .forms import MovimientoUploadForm
from .models import Caso
from .models import ExpedienteSiped
from .models import Movimiento
from .models import Tarea

logger = logging.getLogger(__name__)


class CasoListView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = "casos/caso_list.html"
    context_object_name = "casos"
    paginate_by = 25


class ExpedienteSIPEDListView(LoginRequiredMixin, ListView):
    model = ExpedienteSiped
    template_name = "casos/expediente_siped_list.html"
    context_object_name = "expedientes"
    paginate_by = 25
    ordering = ["-fec_ult_mov"]


class ExpedienteSIPEDDetailView(LoginRequiredMixin, DetailView):
    model = ExpedienteSiped
    template_name = "casos/expediente_siped_detail.html"
    context_object_name = "expediente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movimientos"] = self.object.movimientos.all().order_by(
            "-fecha_presentacion",
        )
        return context


class ExpedienteUploadView(LoginRequiredMixin, FormView):
    template_name = "casos/expediente_upload.html"
    form_class = ExpedienteUploadForm
    success_url = reverse_lazy("casos:expediente_list")

    def form_valid(self, form):
        csv_file = form.cleaned_data["archivo_csv"]

        if not csv_file.name.lower().endswith(".csv"):
            messages.error(self.request, "El archivo debe tener extensión .csv")
            return self.form_invalid(form)

        try:
            content = csv_file.read()
            try:
                data_set = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                data_set = content.decode("latin-1")

            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)

            creados = 0
            actualizados = 0

            for row in reader:
                expediente_nro = row.get("expediente", "").strip()
                if not expediente_nro:
                    continue

                fec_ult_mov = None
                fecha_str = row.get("fec_ult_mov", "")
                if fecha_str:
                    with contextlib.suppress(ValueError):
                        fec_ult_mov = datetime.strptime(  # noqa: DTZ007
                            fecha_str,
                            "%d/%m/%Y",
                        ).date()

                partes = None
                partes_str = row.get("partes", "")
                if partes_str and partes_str.isdigit():
                    partes = int(partes_str)

                _, created = ExpedienteSiped.objects.update_or_create(
                    expediente=expediente_nro,
                    defaults={
                        "caratula": row.get("caratula", "")[:500],
                        "dependencia": row.get("dependencia", "")[:255],
                        "estado": row.get("estado", "")[:100],
                        "fec_ult_mov": fec_ult_mov,
                        "link_detalle": row.get("link_detalle", "")[:500],
                        "localidad": row.get("localidad", "")[:100],
                        "secretaria": row.get("secretaria", "")[:100],
                        "partes": partes,
                    },
                )

                if created:
                    creados += 1
                else:
                    actualizados += 1

            messages.success(
                self.request,
                f"Importación exitosa: {creados} creados, {actualizados} actualizados.",
            )

        except Exception as e:  # noqa: BLE001
            messages.error(self.request, f"Error procesando el archivo: {e}")
            return self.form_invalid(form)

        return super().form_valid(form)


class MovimientoExpedienteUploadView(LoginRequiredMixin, FormView):
    template_name = "casos/movimiento_upload.html"
    form_class = MovimientoUploadForm

    def get_success_url(self):
        return reverse("casos:expediente_detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expediente = get_object_or_404(ExpedienteSiped, pk=self.kwargs["pk"])
        context["titulo"] = f"Importar Movimientos: {expediente.expediente}"
        context["ayuda"] = (
            "Sube el archivo CSV. "
            "El sistema reparará automáticamente las líneas cortadas."
        )
        return context

    def parse_datetime(self, date_str):
        if not date_str:
            return None
        date_str = " ".join(date_str.split())
        if not date_str:
            return None

        formatos = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formatos:
            try:
                dt = datetime.strptime(date_str, fmt)  # noqa: DTZ007
                return make_aware(dt)
            except ValueError:
                continue
        return None

    def reparar_csv_en_memoria(self, content_str):
        lines = content_str.splitlines()
        if not lines:
            return io.StringIO("")

        fixed_lines = []
        exp_pattern = re.compile(r"^\d+/\d+,")

        if len(lines) > 0:
            fixed_lines.append(lines[0])

        current_line = ""

        for raw_line in lines[1:]:
            line = raw_line.strip()
            if not line:
                continue

            if exp_pattern.match(line):
                if current_line:
                    fixed_lines.append(current_line)
                current_line = line
            else:
                current_line += " " + line

        if current_line:
            fixed_lines.append(current_line)

        return io.StringIO("\n".join(fixed_lines))

    def form_valid(self, form):
        csv_file = form.cleaned_data["archivo_csv"]
        expediente = get_object_or_404(ExpedienteSiped, pk=self.kwargs["pk"])

        if not csv_file.name.lower().endswith(".csv"):
            messages.error(self.request, "El archivo debe ser un CSV.")
            return self.form_invalid(form)

        creados = 0
        actualizados = 0

        try:
            content = csv_file.read()
            try:
                content_str = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                content_str = content.decode("latin-1")

            io_reparado = self.reparar_csv_en_memoria(content_str)
            reader = csv.DictReader(io_reparado)

            with transaction.atomic():
                for row in reader:
                    nombre_escrito = row.get("nombre_escrito", "").strip()

                    f_pres = self.parse_datetime(row.get("fecha_presentacion"))
                    f_firma = self.parse_datetime(row.get("fecha_firma"))
                    f_pub = self.parse_datetime(row.get("fecha_publicacion"))

                    defaults_data = {
                        "link_escrito": row.get("link_escrito", "")[:500],
                        "fecha_presentacion": f_pres,
                        "tipo": row.get("tipo", "")[:100],
                        "estado": row.get("estado", "")[:100],
                        "generado_por": row.get("generado_por", "")[:255],
                        "descripcion": row.get("descripcion", ""),
                        "fecha_firma": f_firma,
                        "fecha_publicacion": f_pub,
                    }

                    if nombre_escrito:
                        _, created = Movimiento.objects.update_or_create(
                            expediente=expediente,
                            nombre_escrito=nombre_escrito,
                            defaults=defaults_data,
                        )
                    elif f_pres:
                        _, created = Movimiento.objects.update_or_create(
                            expediente=expediente,
                            fecha_presentacion=f_pres,
                            tipo=row.get("tipo", "")[:100],
                            defaults={**defaults_data, "nombre_escrito": ""},
                        )
                    else:
                        Movimiento.objects.create(
                            expediente=expediente,
                            **defaults_data,
                        )
                        created = True

                    if created:
                        creados += 1
                    else:
                        actualizados += 1

            messages.success(
                self.request,
                f"Proceso completado con corrección automática de líneas: "
                f"{creados} nuevos, {actualizados} actualizados.",
            )

        except Exception as e:  # noqa: BLE001
            messages.error(self.request, f"Error procesando archivo: {e}")
            return self.form_invalid(form)

        return super().form_valid(form)


class MatrizTareasView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = "casos/matriz_tareas.html"
    context_object_name = "casos"

    def get_queryset(self):
        return Caso.objects.prefetch_related("tareas").all().order_by("-id")


class TareaUpdateView(LoginRequiredMixin, UpdateView):
    model = Tarea
    fields = [
        "titulo",
        "descripcion",
        "estado",
        "responsable",
        "fecha_inicio",
        "fecha_limite",
        "fecha_terminacion",
    ]
    template_name = "casos/modal_tarea_form.html"

    def get_success_url(self):
        return reverse_lazy("casos:matriz")


class TareaCreateView(LoginRequiredMixin, CreateView):
    model = Tarea
    fields = [
        "titulo",
        "descripcion",
        "estado",
        "responsable",
        "fecha_inicio",
        "fecha_limite",
        "fecha_terminacion",
    ]
    template_name = "casos/modal_tarea_form.html"

    def form_valid(self, form):
        caso = get_object_or_404(Caso, pk=self.kwargs["caso_id"])
        form.instance.caso = caso
        form.instance.creado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("casos:matriz")


class CasoDetailModalView(LoginRequiredMixin, DetailView):
    """
    Muestra la información del Caso y su Cliente en el modal.
    No requiere modificar modelos, solo renderiza un template parcial.
    """

    model = Caso
    template_name = "casos/modal_caso_detail.html"
    context_object_name = "caso"
