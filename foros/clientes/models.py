from django.db import models


class Cliente(models.Model):
    """
    Representa a un cliente del estudio, que puede ser
    una persona física o una empresa.
    """

    nombre_razon_social = models.CharField(
        max_length=255,
        help_text="Nombre completo o Razón Social",
    )
    cuit_cuil = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        help_text="CUIT/CUIL sin guiones.",
    )
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    domicilio = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre_razon_social
