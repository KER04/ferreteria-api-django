from django.db import models
from apps.autenticacion.models import *
from apps.inventario.models import *
# Register your models here.

class Renta(models.Model):
    rent_id = models.AutoField(primary_key=True)
    renta_fecha_prestamo = models.DateField()
    renta_fecha_devolucion = models.DateField(blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='rentas')

    class Meta:
        db_table = "Rentas"
        verbose_name = "Renta"
        verbose_name_plural = "Rentas"

    def __str__(self):
        return f"Renta {self.rent_id} - {self.usuario}"
    


class TipoPago(models.Model):
    tipa_id = models.AutoField(primary_key=True)
    tipa_nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_pago"
        verbose_name = "Tipo de pago"
        verbose_name_plural = "Tipos de pago"

    def __str__(self):
        return self.tipa_nombre


class Estado(models.Model):
    esta_id = models.AutoField(primary_key=True)
    esta_nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "estado"
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

    def __str__(self):
        return self.esta_nombre


class Pago(models.Model):
    pago_id = models.AutoField(primary_key=True)

    # Montos
    pago_total = models.DecimalField(max_digits=12, decimal_places=2)
    pago_descuento = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    pago_total_cancelado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Fechas
    pago_fecha_facturacion = models.DateField(blank=True, null=True)
    pago_fecha_limite_pago = models.DateField(blank=True, null=True)

    # Llaver foraneas
    tipo_pago = models.ForeignKey(
        TipoPago,
        on_delete=models.PROTECT,
        db_column="tipo_pago_tipa_id",
        related_name="pagos",
    )
    estado = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        db_column="estado_esta_id",
        related_name="pagos",
    )
    renta = models.ForeignKey(
        Renta,
        on_delete=models.CASCADE,
        db_column="Rentas_rent_id",
        related_name="pagos",
    )

    class Meta:
        db_table = "pagos"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago {self.pago_id} - Renta {self.renta_id}"
    


class RentaProducto(models.Model):
    renta = models.ForeignKey(
        Renta,
        on_delete=models.CASCADE,
        db_column="Rentas_rent_id",
        related_name="renta_productos"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        db_column="productos_prod_id",
        related_name="renta_productos"
    )
    tipo_categoria = models.ForeignKey(
        TipoCategoria,
        on_delete=models.PROTECT,
        db_column="productos_tipo_categoria_tipr_id",
        related_name="renta_productos"
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        db_column="productos_marca_marca_id",
        related_name="renta_productos"
    )
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.PROTECT,
        db_column="productos_prestamo_pres_ID",
        related_name="renta_productos"
    )

    class Meta:
        db_table = "Rentas_has_productos"
        verbose_name = "Relación Renta-Producto"
        verbose_name_plural = "Relaciones Renta-Producto"
        unique_together = ("renta", "producto")  # evita duplicados

    def __str__(self):
        return f"Renta {self.renta.rent_id} → Producto {self.producto.prod_nombre}"
