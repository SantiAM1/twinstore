from django.db import models
from django.utils.timezone import localtime
class DolarConfiguracion(models.Model):
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        fecha_local = localtime(self.fecha_actualizacion)
        return f"Dolar: {self.valor}, Actualizado el {fecha_local.strftime('%d/%m/%Y a las %H:%M hs')}"
    
    class Meta:
        verbose_name = "Configuración de dólar"
        verbose_name_plural = "⚙️ Configuración . Dolar"

class ModoMantenimiento(models.Model):
    activo = models.BooleanField(default=False)

    def __str__(self):
        return "❌ Sitio en mantenimiento" if self.activo else "✅ Sitio activo"

    class Meta:
        verbose_name = "Modo de mantenimiento"
        verbose_name_plural = "⚙️ Configuración · Mantenimiento"
