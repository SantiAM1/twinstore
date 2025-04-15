from django.db import models

class ModoMantenimiento(models.Model):
    activo = models.BooleanField(default=False)

    def __str__(self):
        return "Sitio en mantenimiento" if self.activo else "Sitio activo"

    class Meta:
        verbose_name = "Modo Mantenimiento"
        verbose_name_plural = "Modo Mantenimiento"
