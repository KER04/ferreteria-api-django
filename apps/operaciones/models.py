from django.core.exceptions import ValidationError
from django.db import models

from apps.autenticacion.models import Usuario
from apps.inventario.models import Producto


# ─────────────────────────────────────────────
# OPERACIÓN
# ─────────────────────────────────────────────
class Operacion(models.Model):

    class TipoOperacion(models.TextChoices):
        VENTA    = "venta",    "Venta"
        PRESTAMO = "prestamo", "Préstamo"

    class EstadoOperacion(models.TextChoices):
        ACTIVA     = "activa",     "Activa"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA  = "cancelada",  "Cancelada"

    codigo_operacion = models.CharField(max_length=20, unique=True, blank=True)
    tipo_operacion   = models.CharField(max_length=10, choices=TipoOperacion.choices)
    estado           = models.CharField(
        max_length=12, choices=EstadoOperacion.choices,
        default=EstadoOperacion.ACTIVA,
    )
    usuario         = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="operaciones",
    )
    cliente         = models.CharField(max_length=150, blank=True, null=True)
    fecha_operacion  = models.DateField(auto_now_add=True)
    fecha_devolucion = models.DateField(blank=True, null=True)
    observaciones   = models.TextField(blank=True, null=True)

    class Meta:
        db_table            = "operacion"
        verbose_name        = "Operación"
        verbose_name_plural = "Operaciones"
        ordering            = ["-fecha_operacion", "-id"]
        indexes = [
            # Filtros frecuentes por estado y tipo, y el reporte de vencidos
            models.Index(fields=["estado"]),
            models.Index(fields=["tipo_operacion", "estado"]),
            models.Index(fields=["fecha_devolucion"]),
        ]

    def _generar_codigo(self) -> str:
        prefijo = "VEN" if self.tipo_operacion == self.TipoOperacion.VENTA else "PRE"
        ultimo  = (
            Operacion.objects
            .filter(codigo_operacion__startswith=prefijo)
            .exclude(pk=self.pk)
            .order_by("codigo_operacion")
            .values_list("codigo_operacion", flat=True)
            .last()
        )
        n = 1
        if ultimo:
            try:
                n = int(ultimo.split("-")[-1]) + 1
            except ValueError:
                pass
        return f"{prefijo}-{n:04d}"

    def save(self, *args, **kwargs):
        if not self.codigo_operacion:
            self.codigo_operacion = self._generar_codigo()
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(d.subtotal for d in self.detalles.all())

    def __str__(self):
        return f"{self.codigo_operacion} | {self.get_tipo_operacion_display()} | {self.cliente or self.usuario}"


# ─────────────────────────────────────────────
# DETALLE OPERACIÓN
# ─────────────────────────────────────────────
class DetalleOperacion(models.Model):
    operacion       = models.ForeignKey(
        Operacion, on_delete=models.CASCADE, related_name="detalles",
    )
    producto        = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="detalles_operacion",
    )
    cantidad        = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal        = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    # ── seguimiento de devoluciones parciales ──
    # Cuántas unidades ya fueron devueltas (se incrementa con cada Devolucion)
    cantidad_devuelta = models.PositiveIntegerField(
        default=0, editable=False,
        help_text="Acumulado de unidades devueltas sobre este detalle.",
    )

    class Meta:
        db_table        = "detalle_operacion"
        verbose_name    = "Detalle de operación"
        verbose_name_plural = "Detalles de operación"
        unique_together = ("operacion", "producto")

    @property
    def cantidad_pendiente(self) -> int:
        """Unidades que aún no se han devuelto."""
        return self.cantidad - self.cantidad_devuelta

    @property
    def devolucion_completa(self) -> bool:
        return self.cantidad_devuelta >= self.cantidad

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor que cero."})

        producto  = self.producto
        tipo_op   = self.operacion.tipo_operacion
        permitida = producto.tipo_operacion_permitida

        if permitida != "mixto" and permitida != tipo_op:
            raise ValidationError(
                f"El producto '{producto}' solo permite "
                f"'{producto.get_tipo_operacion_permitida_display()}'."
            )
        if self.cantidad > producto.prod_cantidad_disponible:
            raise ValidationError(
                {"cantidad": (
                    f"Stock insuficiente para '{producto.prod_nombre}'. "
                    f"Disponible: {producto.prod_cantidad_disponible}, "
                    f"solicitado: {self.cantidad}."
                )}
            )

    def save(self, *args, **kwargs):
        # Solo deriva un campo propio; el ajuste de stock vive en services.py
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.operacion.codigo_operacion} → {self.producto.prod_nombre} x{self.cantidad}"


# ─────────────────────────────────────────────
# DEVOLUCIÓN  (ForeignKey, no OneToOneField)
# ─────────────────────────────────────────────
class Devolucion(models.Model):
    """
    Permite devoluciones PARCIALES y MÚLTIPLES sobre el mismo detalle.

    Diseño clave:
      - ForeignKey (no OneToOneField) → múltiples devoluciones por detalle.
      - DetalleOperacion.cantidad_devuelta acumula el total devuelto.
      - El clean() valida que no se devuelva más de lo pendiente.
    """

    class EstadoDevolucion(models.TextChoices):
        BUENO   = "bueno",   "Buen estado"
        DAÑADO  = "dañado",  "Dañado"
        PERDIDO = "perdido", "Perdido"

    # ForeignKey en lugar de OneToOneField → permite múltiples devoluciones
    detalle          = models.ForeignKey(
        DetalleOperacion,
        on_delete=models.PROTECT,
        related_name="devoluciones",          # plural, no singular
    )
    fecha_devolucion  = models.DateField(auto_now_add=True)
    cantidad_devuelta = models.PositiveIntegerField()
    estado_devolucion = models.CharField(
        max_length=10,
        choices=EstadoDevolucion.choices,
        default=EstadoDevolucion.BUENO,
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table            = "devolucion"
        verbose_name        = "Devolución"
        verbose_name_plural = "Devoluciones"
        ordering            = ["-fecha_devolucion", "-id"]

    def clean(self):
        # Solo préstamos tienen devolución
        if self.detalle.operacion.tipo_operacion != Operacion.TipoOperacion.PRESTAMO:
            raise ValidationError("Solo se pueden registrar devoluciones de préstamos.")

        if self.cantidad_devuelta <= 0:
            raise ValidationError(
                {"cantidad_devuelta": "La cantidad a devolver debe ser mayor que cero."}
            )

        # ── validación clave: respetar el pendiente, no el total ──
        pendiente = self.detalle.cantidad_pendiente
        if self.cantidad_devuelta > pendiente:
            raise ValidationError(
                {"cantidad_devuelta": (
                    f"Solo quedan {pendiente} unidad(es) pendiente(s) de devolución "
                    f"en este detalle."
                )}
            )

    # El ajuste de stock y el acumulado en el detalle viven en services.py
    # (registrar_devolucion). El modelo solo guarda datos y valida en clean().

    def __str__(self):
        return (
            f"Dev/{self.detalle.operacion.codigo_operacion} "
            f"— {self.detalle.producto.prod_nombre} "
            f"x{self.cantidad_devuelta} ({self.estado_devolucion})"
        )
