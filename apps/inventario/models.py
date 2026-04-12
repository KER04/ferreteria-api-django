from django.db import models


class TipoCategoria(models.Model):
    tipr_id = models.AutoField(primary_key=True)
    tipr_nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_categoria"
        verbose_name = "Tipo de Categoría"
        verbose_name_plural = "Tipos de Categoría"

    def __str__(self):
        return self.tipr_nombre


class Marca(models.Model):
    marca_id = models.AutoField(primary_key=True)
    marca_nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "marca"
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.marca_nombre


class Prestamo(models.Model):
    pres_id = models.AutoField(primary_key=True, db_column="pres_ID")
    pres_nombre = models.CharField(max_length=45)
    tipo_prestamo = models.CharField(max_length=45)

    class Meta:
        db_table = "prestamo"
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"

    def __str__(self):
        return f"{self.pres_nombre} ({self.tipo_prestamo})"
    



class Producto(models.Model):
    prod_id = models.AutoField(primary_key=True)
    prod_nombre = models.CharField(max_length=45)
    prod_modelo = models.CharField(max_length=45, blank=True, null=True)
    prod_foto = models.CharField(max_length=45, blank=True, null=True)
    prod_valor_unitario = models.CharField(max_length=45)
    tipo_prestamos = models.CharField(max_length=45, blank=True, null=True)
    prod_estado = models.CharField(max_length=45, blank=True, null=True)
    prod_cantidad_disponible = models.CharField(max_length=45, blank=True, null=True)
    prod_cantidad_prestada = models.CharField(max_length=45, blank=True, null=True)
    prod_cantidad_total = models.CharField(max_length=45, blank=True, null=True)

    # Relaciones
    tipo_categoria = models.ForeignKey(
        TipoCategoria,
        on_delete=models.PROTECT,
        db_column="tipo_categoria_tipr_id",
        related_name="productos"
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        db_column="marca_marca_id",
        related_name="productos"
    )
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        db_column="prestamo_pres_ID",
        related_name="productos"
    )

    class Meta:
        db_table = "productos"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.prod_nombre} ({self.prod_modelo})"
