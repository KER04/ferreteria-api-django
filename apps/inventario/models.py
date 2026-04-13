from django.db import models
from django.core.exceptions import ValidationError


# ─────────────────────────────────────────────
# TIPO CATEGORÍA
# ─────────────────────────────────────────────
class TipoCategoria(models.Model):
    tipr_id     = models.AutoField(primary_key=True)
    tipr_nombre = models.CharField(max_length=45)

    class Meta:
        db_table            = "tipo_categoria"
        verbose_name        = "Tipo de Categoría"
        verbose_name_plural = "Tipos de Categoría"

    def __str__(self):
        return self.tipr_nombre


# ─────────────────────────────────────────────
# MARCA
# ─────────────────────────────────────────────
class Marca(models.Model):
    marca_id     = models.AutoField(primary_key=True)
    marca_nombre = models.CharField(max_length=45)

    class Meta:
        db_table            = "marca"
        verbose_name        = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.marca_nombre


# ─────────────────────────────────────────────
# PRÉSTAMO (catálogo — no eliminar)
# ─────────────────────────────────────────────
class Prestamo(models.Model):
    pres_id       = models.AutoField(primary_key=True, db_column="pres_ID")
    pres_nombre   = models.CharField(max_length=45)
    tipo_prestamo = models.CharField(max_length=45)

    class Meta:
        db_table            = "prestamo"
        verbose_name        = "Tipo de préstamo"
        verbose_name_plural = "Tipos de préstamo"

    def __str__(self):
        return f"{self.pres_nombre} ({self.tipo_prestamo})"


# ─────────────────────────────────────────────
# PRODUCTO
# ─────────────────────────────────────────────
class Producto(models.Model):

    class Estado(models.TextChoices):
        DISPONIBLE    = "Disponible",    "Disponible"
        PRESTADO      = "Prestado",      "Prestado"
        MANTENIMIENTO = "Mantenimiento", "Mantenimiento"
        DAÑADO        = "Dañado",        "Dañado"
        AGOTADO       = "Agotado",       "Agotado"

    class TipoOperacionPermitida(models.TextChoices):
        VENTA    = "venta",   "Solo venta"
        PRESTAMO = "prestamo","Solo préstamo"
        MIXTO    = "mixto",   "Venta y préstamo"

    # ── identificación ───────────────────────
    prod_id         = models.AutoField(primary_key=True)
    prod_nombre     = models.CharField(max_length=100)
    prod_modelo     = models.CharField(max_length=100, blank=True, null=True)
    descripcion     = models.TextField(blank=True, null=True)
    proveedor       = models.CharField(max_length=100, blank=True, null=True)

    prod_foto = models.ImageField(
        upload_to="productos/fotos/",
        blank=True, null=True,
    )
    codigo_producto = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text="Auto-generado: CAT-MAR-001",
    )

    # ── operaciones permitidas ────────────────
    tipo_operacion_permitida = models.CharField(
        max_length=10,
        choices=TipoOperacionPermitida.choices,
        default=TipoOperacionPermitida.MIXTO,
        help_text="Define si el producto se vende, se presta o ambos.",
    )

    # ── valor ────────────────────────────────
    prod_valor_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    # ── estado ───────────────────────────────
    prod_estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )

    # ── cantidades ───────────────────────────
    prod_cantidad_disponible = models.IntegerField(default=0)
    prod_cantidad_prestada   = models.IntegerField(default=0, editable=False)
    prod_cantidad_en_mantenimiento = models.IntegerField(default=0, editable=False)
    prod_cantidad_total      = models.IntegerField(default=0, editable=False)

    # ── relaciones ───────────────────────────
    tipo_categoria = models.ForeignKey(
        TipoCategoria,
        on_delete=models.PROTECT,
        db_column="tipo_categoria_tipr_id",
        related_name="productos",
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        db_column="marca_marca_id",
        related_name="productos",
    )
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        db_column="prestamo_pres_ID",
        related_name="productos",
    )

    class Meta:
        db_table            = "productos"
        verbose_name        = "Producto"
        verbose_name_plural = "Productos"

    # ── helpers ──────────────────────────────
    def _generar_codigo(self) -> str:
        cat    = (self.tipo_categoria.tipr_nombre[:3]).upper() if self.tipo_categoria_id else "GEN"
        mar    = (self.marca.marca_nombre[:3]).upper()         if self.marca_id else "GEN"
        prefix = f"{cat}-{mar}-"
        ultimo = (
            Producto.objects
            .filter(codigo_producto__startswith=prefix)
            .exclude(pk=self.pk)
            .order_by("codigo_producto")
            .values_list("codigo_producto", flat=True)
            .last()
        )
        n = 1
        if ultimo:
            try:
                n = int(ultimo.split("-")[-1]) + 1
            except ValueError:
                pass
        return f"{prefix}{n:03d}"

    def _calcular_estado(self) -> str:
        if (self.prod_cantidad_disponible or 0) == 0:
            return self.Estado.AGOTADO
        if self.prod_estado == self.Estado.AGOTADO:
            return self.Estado.DISPONIBLE
        return self.prod_estado

    def save(self, *args, **kwargs):
        self.prod_cantidad_total = (
            (self.prod_cantidad_disponible or 0) +
            (self.prod_cantidad_prestada   or 0) +
            (self.prod_cantidad_en_mantenimiento or 0)
        )
        self.prod_estado = self._calcular_estado()
        if not self.codigo_producto:
            self.codigo_producto = self._generar_codigo()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo_producto}] {self.prod_nombre}"