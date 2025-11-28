import csv
import re
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from foros.casos.models import Caso
from foros.casos.models import Tarea
from foros.clientes.models import Cliente

User = get_user_model()
MAX_TITLE_LENGTH = 47


class Command(BaseCommand):
    help = (
        "Importa datos para testing manual. Limpia caracteres nulos y rellena "
        "datos faltantes."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Ruta al archivo CSV")

    def inferir_estado(self, descripcion):
        """
        Lógica de colores basada en tiempos verbales/palabras clave.
        """
        texto = descripcion.lower()

        if "esperando" in texto:
            return Tarea.Estado.ESPERANDO  # Azul

        if "controlar" in texto:
            return Tarea.Estado.A_CONTROLAR  # Amarillo

        palabras_verde = [
            "notificado",
            "diligenciado",
            "acreditado",
            "presentado",
            "regularon",
            "trabado",
            "contestó",
            "ok",
            "listo",
            "agregado",
        ]

        for p in palabras_verde:
            if p in texto:
                return Tarea.Estado.REALIZADA

        if re.search(r"(ado|ida|ido|ada)\b", texto):
            return Tarea.Estado.REALIZADA

        return Tarea.Estado.A_REALIZAR

    def _clean_null_bytes(self, file_handle):
        for line in file_handle:
            yield line.replace("\0", "")

    def process_csv(self, csv_path, usuario, cliente_dummy):
        hoy = timezone.now()
        vencimiento = hoy + timedelta(days=7)

        with csv_path.open(encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(self._clean_null_bytes(f))

            try:
                encabezados = next(reader)
            except StopIteration:
                self.stdout.write(
                    self.style.ERROR("El archivo CSV está vacío."),
                )
                return

            casos_map = {}

            for idx, raw_nombre in enumerate(encabezados):
                nombre_caso = raw_nombre.strip()
                if not nombre_caso:
                    continue

                caso, _ = Caso.objects.get_or_create(
                    titulo_interno=nombre_caso[:255],
                    defaults={
                        "cliente": cliente_dummy,
                        "responsable": usuario,
                        "naturaleza": Caso.Naturaleza.JUDICIAL,
                    },
                )
                casos_map[idx] = caso

            tareas_count = 0
            for row in reader:
                for idx, celda in enumerate(row):
                    if celda and celda.strip() and idx in casos_map:
                        texto = celda.strip()
                        caso_obj = casos_map[idx]
                        estado = self.inferir_estado(texto)

                        if len(texto) > MAX_TITLE_LENGTH:
                            titulo = texto[:MAX_TITLE_LENGTH] + "..."
                        else:
                            titulo = texto

                        Tarea.objects.create(
                            caso=caso_obj,
                            titulo=titulo,
                            descripcion=texto,
                            estado=estado,
                            responsable=usuario,
                            creado_por=usuario,
                            fecha_inicio=hoy,
                            fecha_limite=vencimiento,
                        )
                        tareas_count += 1

            msg = (
                f"Listo. Se importaron {len(casos_map)} Casos y {tareas_count} Tareas."
            )
            self.stdout.write(self.style.SUCCESS(msg))

    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"])

        if not csv_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Archivo no encontrado: {csv_path}"),
            )
            return

        usuario = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not usuario:
            self.stdout.write(
                self.style.ERROR(
                    "No hay usuarios. Crea un superusuario primero.",
                ),
            )
            return

        cliente_dummy, _ = Cliente.objects.get_or_create(
            nombre_razon_social="CLIENTE TEST - SIN ASIGNAR",
            defaults={"email": "test@localhost", "telefono": "000000"},
        )

        self.stdout.write(
            f"Importando con usuario: {usuario} y Cliente: {cliente_dummy}...",
        )

        try:
            self.process_csv(csv_path, usuario, cliente_dummy)
        except Exception as e:  # noqa: BLE001
            self.stdout.write(
                self.style.ERROR(f"Error procesando el archivo: {e!s}"),
            )
