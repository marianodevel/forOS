from django.conf import settings
from django.db import models

from foros.clientes.models import Cliente


# --- Modelo 2 (de 5): ExpedienteSiped ---
# Representa el expediente externo/oficial (ej. SIPED)
# Contiene los campos del CSV "expedientes_completos.csv"
class ExpedienteSiped(models.Model):
    """
    El registro oficial/externo del SIPED.
    Los campos coinciden con los del CSV "expedientes_completos.csv".
    """

    # --- Datos del Expediente (SIPED) ---
    expediente = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nro. oficial del expediente (Ej: 19827/2025)",
    )
    link_detalle = models.URLField(max_length=500, blank=True)
    caratula = models.CharField(
        max_length=500,
        blank=True,
        help_text="Carátula oficial (Ej: PEREZ C/ GOMEZ S/ D Y P)",
    )
    partes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Campo 'partes' del CSV",
    )
    estado = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: A DESPACHO, PUBLICADO",
    )
    fec_ult_mov = models.DateField(null=True, blank=True)
    localidad = models.CharField(max_length=100, blank=True)
    dependencia = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ej: Juzgado Civil Nro 1",
    )
    secretaria = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Expediente SIPED"
        verbose_name_plural = "Expedientes SIPED"

    def __str__(self):
        return f"{self.expediente} - {self.dependencia or ''}"


# --- Modelo 3 (de 5): Caso ---
# Representa nuestro legajo interno
class Caso(models.Model):
    """
    Nuestro legajo interno. Es el corazón del sistema.
    """

    class Naturaleza(models.TextChoices):
        JUDICIAL = "JUDICIAL", "Judicial"
        EXTRAJUDICIAL = "EXTRAJUDICIAL", "Extrajudicial"
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"

    # --- Relaciones ---
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="casos",
    )
    expediente = models.ForeignKey(
        ExpedienteSiped,  # <-- Actualizado nombre de clase
        on_delete=models.SET_NULL,  # Un caso puede tener un exp. externo
        blank=True,
        null=True,
        related_name="casos",
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="casos_responsable",
    )

    # --- Datos del Caso ---
    titulo_interno = models.CharField(
        max_length=255,
        help_text="Nombre descriptivo interno (Ej: Sucesión Pérez)",
    )
    naturaleza = models.CharField(
        max_length=20,
        choices=Naturaleza.choices,
        default=Naturaleza.JUDICIAL,
    )
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Caso"
        verbose_name_plural = "Casos"

    def __str__(self):
        return self.titulo_interno


# --- Modelo 4 (de 5): Tarea ---
# Representa CADA movimiento INTERNO del estudio (tareas, notas, etc.)
class Tarea(models.Model):
    """
    Cada una de las novedades o tareas INTERNAS asociadas a un Caso.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        A_REVISAR = "A_REVISAR", "A revisar"
        COMPLETADO = "COMPLETADO", "Completado"

    # --- Relaciones Internas ---
    caso = models.ForeignKey(
        Caso,
        on_delete=models.CASCADE,  # Se liga a NUESTRO caso
        related_name="tareas",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tareas_creadas",
    )

    # --- Datos Internos ---
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        help_text="Estado interno de la tarea",
    )

    class Meta:
        verbose_name = "Tarea Interna"
        verbose_name_plural = "Tareas Internas"
        ordering = ["-fecha"]  # El más nuevo primero

    def __str__(self):
        return f"{self.fecha.strftime('%Y-%m-%d')} - {self.descripcion[:40]}..."


# --- Modelo 5 (de 5): Movimiento ---
# Representa CADA movimiento del CSV "19827-2025..."
class Movimiento(models.Model):
    """
    Cada uno de los movimientos del sistema externo (SIPED),
    asociado a un ExpedienteSiped.
    """

    # --- Relación ---
    expediente = models.ForeignKey(
        ExpedienteSiped,  # <-- Actualizado nombre de clase
        on_delete=models.CASCADE,  # Se liga al EXPEDIENTE externo
        related_name="movimientos",
    )

    # --- Campos del CSV (SIPED) ---
    nombre_escrito = models.CharField(max_length=100, blank=True)
    link_escrito = models.URLField(max_length=500, blank=True)
    fecha_presentacion = models.DateTimeField(null=True, blank=True)
    tipo = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: ESCRITO, ESTESE",
    )
    estado = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: PUBLICADO",
    )
    generado_por = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ej: JUZGADO, o nombre de abogado",
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Campo 'descripcion' del CSV",
    )
    fecha_firma = models.DateTimeField(null=True, blank=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Movimiento SIPED"
        verbose_name_plural = "Movimientos SIPED"
        ordering = ["-fecha_presentacion"]

    def __str__(self):
        return f"{self.fecha_presentacion} - {self.tipo}"
