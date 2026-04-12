from django.db import models
from apps.inventario.models import *
from apps.renta.models import *
# Create your models here.


class Costo(models.Model):
    cost_id = models.AutoField(primary_key=True)
    cost_total = models.CharField(max_length=45)                
    cost_partes_afectadas = models.CharField(max_length=45, blank=True, null=True)
    cost_fecha_pago = models.DateField(max_length=45, blank=True, null=True)  

    class Meta:
        db_table = "costo"
        verbose_name = "Costo"
        verbose_name_plural = "Costos"

    def __str__(self):
        return f"Costo {self.cost_id} - {self.cost_total}"


class TipoMantenimiento(models.Model):
    tima_id = models.AutoField(primary_key=True)
    tima_nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_mantenimiento"
        verbose_name = "Tipo de mantenimiento"
        verbose_name_plural = "Tipos de mantenimiento"

    def __str__(self):
        return self.tima_nombre


class Mantenimiento(models.Model):
    mant_id = models.AutoField(primary_key=True)

    # Campos propios
    mant_fecha = models.DateField(max_length=45, blank=True, null=True)       # 👈 DateField si quieres fecha real
    mant_descripcion = models.CharField(max_length=45, blank=True, null=True)

    # Relaciones 
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        db_column="productos_prod_id",
        related_name="mantenimientos",
    )
    tipo_mantenimiento = models.ForeignKey(
        TipoMantenimiento,
        on_delete=models.PROTECT,
        db_column="tipo_mantenimiento_tima_id",
        related_name="mantenimientos",
    )
    costo = models.ForeignKey(
        Costo,
        on_delete=models.PROTECT,
        db_column="costo_cost_id",
        related_name="mantenimientos",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="Usuario_usua_id",
        related_name="mantenimientos",
    )

    class Meta:
        db_table = "mantenimiento"
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"

    def __str__(self):
        return f"Mant {self.mant_id} - {self.producto} - {self.tipo_mantenimiento}"