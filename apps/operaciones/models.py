from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
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
        self.subtotal = self.cantidad * self.precio_unitario
        es_nuevo = self._state.adding

        if es_nuevo:
            self.full_clean()
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(pk=self.producto_id)

                if self.operacion.tipo_operacion == Operacion.TipoOperacion.VENTA:
                    producto.prod_cantidad_disponible -= self.cantidad
                else:
                    producto.prod_cantidad_disponible -= self.cantidad
                    producto.prod_cantidad_prestada   += self.cantidad

                producto.save()
                super().save(*args, **kwargs)
        else:
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

    def save(self, *args, **kwargs):
        if not self._state.adding:
            # Las devoluciones ya guardadas son inmutables
            super().save(*args, **kwargs)
            return

        self.full_clean()

        with transaction.atomic():
            # Lock del producto para evitar race conditions
            producto = Producto.objects.select_for_update().get(
                pk=self.detalle.producto_id
            )

            # 1) Ajustar stock
            producto.prod_cantidad_disponible += self.cantidad_devuelta
            producto.prod_cantidad_prestada   -= self.cantidad_devuelta

            # 2) Actualizar estado del producto
            #    IMPORTANTE: se fija ANTES de llamar producto.save()
            #    para que _calcular_estado() lo respete correctamente.
            if self.estado_devolucion == self.EstadoDevolucion.DAÑADO:
                # Marcar el producto como dañado — _calcular_estado lo preservará
                # porque la lógica solo fuerza Agotado cuando disponible == 0
                # y solo revierte Agotado → Disponible, no toca Dañado.
                producto.prod_estado = Producto.Estado.DAÑADO
            elif self.estado_devolucion == self.EstadoDevolucion.PERDIDO:
                # Perdido: la unidad no vuelve al stock (ya no restamos prestada
                # pero tampoco sumamos disponible); ajuste manual.
                # Revertimos la suma que hicimos arriba.
                producto.prod_cantidad_disponible -= self.cantidad_devuelta
                # El producto queda con menos stock total.

            producto.save()

            # 3) Acumular en el detalle
            self.detalle.cantidad_devuelta += self.cantidad_devuelta
            self.detalle.save(update_fields=["cantidad_devuelta"])

            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Dev/{self.detalle.operacion.codigo_operacion} "
            f"— {self.detalle.producto.prod_nombre} "
            f"x{self.cantidad_devuelta} ({self.estado_devolucion})"
        )