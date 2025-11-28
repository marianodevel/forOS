from django.conf import settings
from django.db import models
from django.utils import timezone

from foros.clientes.models import Cliente


class ExpedienteSiped(models.Model):
    """
    El registro oficial/externo del SIPED.
    Los campos coinciden con los del CSV "expedientes_completos.csv".
    """

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


class Caso(models.Model):
    """
    Nuestro legajo interno. Es el corazón del sistema.
    """

    class Naturaleza(models.TextChoices):
        JUDICIAL = "JUDICIAL", "Judicial"
        EXTRAJUDICIAL = "EXTRAJUDICIAL", "Extrajudicial"
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="casos",
    )
    expediente = models.ForeignKey(
        ExpedienteSiped,
        on_delete=models.SET_NULL,
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


class Tarea(models.Model):
    """
    Cada una de las novedades o tareas INTERNAS asociadas a un Caso.
    """

    class Estado(models.TextChoices):
        A_REALIZAR = "A_REALIZAR", "A Realizar"  # Rojo
        REALIZADA = "REALIZADA", "Realizada"  # Verde
        A_CONTROLAR = "A_CONTROLAR", "A Controlar"  # Amarillo
        ESPERANDO = "ESPERANDO", "Esperando"  # Azul

    caso = models.ForeignKey(
        Caso,
        on_delete=models.CASCADE,
        related_name="tareas",
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tareas_asignadas",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tareas_creadas",
    )

    titulo = models.CharField(max_length=200, help_text="Título corto para la vista")
    descripcion = models.TextField(blank=True)

    fecha_inicio = models.DateField(default=timezone.now)
    fecha_limite = models.DateField(null=True, blank=True)
    fecha_terminacion = models.DateField(null=True, blank=True)

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.A_REALIZAR,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tarea Interna"
        verbose_name_plural = "Tareas Internas"
        ordering = ["fecha_limite", "-fecha_creacion"]

    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"

    @property
    def color_bootstrap(self):
        mapping = {
            self.Estado.A_REALIZAR: "danger",
            self.Estado.REALIZADA: "success",
            self.Estado.A_CONTROLAR: "warning",
            self.Estado.ESPERANDO: "info",
        }
        return mapping.get(self.estado, "secondary")


class Movimiento(models.Model):
    """
    Cada uno de los movimientos del sistema externo (SIPED),
    asociado a un ExpedienteSiped.
    """

    expediente = models.ForeignKey(
        ExpedienteSiped,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )

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
