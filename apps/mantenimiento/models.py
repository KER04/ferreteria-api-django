from django.core.exceptions import ValidationError
from django.db import models

from apps.autenticacion.models import Usuario
from apps.inventario.models import Producto


# ─────────────────────────────────────────────
# COSTO  (sin cambios)
# ─────────────────────────────────────────────
class Costo(models.Model):
    cost_id             = models.AutoField(primary_key=True)
    cost_total          = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Costo total del mantenimiento.",
    )
    cost_partes_afectadas = models.CharField(max_length=200, blank=True, null=True)
    cost_fecha_pago     = models.DateField(blank=True, null=True)

    class Meta:
        db_table            = "costo"
        verbose_name        = "Costo"
        verbose_name_plural = "Costos"

    def __str__(self):
        return f"Costo {self.cost_id} — ${self.cost_total}"


# ─────────────────────────────────────────────
# TIPO MANTENIMIENTO  (sin cambios)
# ─────────────────────────────────────────────
class TipoMantenimiento(models.Model):
    tima_id     = models.AutoField(primary_key=True)
    tima_nombre = models.CharField(max_length=45)

    class Meta:
        db_table            = "tipo_mantenimiento"
        verbose_name        = "Tipo de mantenimiento"
        verbose_name_plural = "Tipos de mantenimiento"

    def __str__(self):
        return self.tima_nombre


# ─────────────────────────────────────────────
# MANTENIMIENTO
# ─────────────────────────────────────────────
class Mantenimiento(models.Model):
    """
    Registra la entrada de unidades dañadas a mantenimiento
    y su salida una vez reparadas (o dadas de baja si no se recuperan).

    Flujo de stock:
      Entrada → prod_cantidad_disponible  -= cantidad
                prod_cantidad_en_mantenimiento += cantidad   (campo nuevo en Producto)
                prod_estado = Mantenimiento (si disponible == 0)

      Salida  → prod_cantidad_en_mantenimiento -= cantidad_recuperada
                prod_cantidad_disponible  += cantidad_recuperada
                prod_cantidad_disponible  -= cantidad_baja  (pérdida total)
    """

    class Estado(models.TextChoices):
        EN_PROCESO  = "en_proceso",  "En proceso"
        FINALIZADO  = "finalizado",  "Finalizado"
        CANCELADO   = "cancelado",   "Cancelado"

    # ── identificación ───────────────────────
    mant_id     = models.AutoField(primary_key=True)
    estado      = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.EN_PROCESO,
    )

    # ── descripción ──────────────────────────
    mant_descripcion = models.TextField(
        blank=True, null=True,
        help_text="Descripción del daño o motivo de ingreso.",
    )

    # ── cantidades ───────────────────────────
    cantidad_ingresada = models.PositiveIntegerField(
        help_text="Unidades que ingresan a mantenimiento.",
    )
    cantidad_recuperada = models.PositiveIntegerField(
        default=0, editable=False,
        help_text="Unidades que salieron reparadas (se registra al finalizar).",
    )
    cantidad_baja = models.PositiveIntegerField(
        default=0, editable=False,
        help_text="Unidades que no se pudieron recuperar (pérdida total).",
    )

    # ── fechas ───────────────────────────────
    fecha_ingreso   = models.DateField(auto_now_add=True)
    fecha_salida    = models.DateField(
        blank=True, null=True,
        help_text="Se llena automáticamente al finalizar.",
    )

    # ── relaciones ───────────────────────────
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
        blank=True, null=True,
        help_text="Se puede asignar el costo al finalizar.",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="Usuario_usua_id",
        related_name="mantenimientos",
    )

    class Meta:
        db_table            = "mantenimiento"
        verbose_name        = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering            = ["-fecha_ingreso", "-mant_id"]
        indexes = [
            models.Index(fields=["estado"]),
        ]

    # ── propiedades calculadas ────────────────
    @property
    def cantidad_pendiente(self) -> int:
        """Unidades aún en mantenimiento (ni recuperadas ni dadas de baja)."""
        return self.cantidad_ingresada - self.cantidad_recuperada - self.cantidad_baja

    # ── validaciones ─────────────────────────
    def clean(self):
        if self.cantidad_ingresada <= 0:
            raise ValidationError(
                {"cantidad_ingresada": "La cantidad debe ser mayor que cero."}
            )
        # Solo validar stock en creación
        if self._state.adding:
            if self.cantidad_ingresada > self.producto.prod_cantidad_disponible:
                raise ValidationError(
                    {"cantidad_ingresada": (
                        f"Stock insuficiente. Disponible: "
                        f"{self.producto.prod_cantidad_disponible}, "
                        f"solicitado: {self.cantidad_ingresada}."
                    )}
                )

    # El ajuste de stock en la entrada vive en services.ingresar_mantenimiento.
    # El modelo solo guarda datos y valida en clean().

    def __str__(self):
        return (
            f"Mant-{self.mant_id:04d} | {self.producto.prod_nombre} "
            f"x{self.cantidad_ingresada} | {self.get_estado_display()}"
        )


# ─────────────────────────────────────────────
# SALIDA DE MANTENIMIENTO
# ─────────────────────────────────────────────
class SalidaMantenimiento(models.Model):
    """
    Registra el resultado final de un mantenimiento:
    cuántas unidades se recuperaron y cuántas se dan de baja.

    Una vez registrada la salida:
      - Las recuperadas vuelven al stock disponible.
      - Las dadas de baja se descuentan permanentemente.
      - El Mantenimiento queda en estado 'Finalizado'.
    """

    mantenimiento     = models.OneToOneField(
        Mantenimiento,
        on_delete=models.PROTECT,
        related_name="salida",
    )
    fecha_salida      = models.DateField(auto_now_add=True)
    cantidad_recuperada = models.PositiveIntegerField(
        help_text="Unidades reparadas que vuelven al stock.",
    )
    cantidad_baja     = models.PositiveIntegerField(
        default=0,
        help_text="Unidades que no se pudieron reparar (pérdida total).",
    )
    observaciones     = models.TextField(blank=True, null=True)
    costo             = models.ForeignKey(
        Costo,
        on_delete=models.PROTECT,
        blank=True, null=True,
        related_name="salidas",
        help_text="Costo final de la reparación (opcional).",
    )

    class Meta:
        db_table            = "salida_mantenimiento"
        verbose_name        = "Salida de mantenimiento"
        verbose_name_plural = "Salidas de mantenimiento"

    def clean(self):
        mant = self.mantenimiento

        # No se puede registrar salida si ya está finalizado
        if mant.estado == Mantenimiento.Estado.FINALIZADO:
            raise ValidationError(
                "Este mantenimiento ya fue finalizado."
            )

        total = self.cantidad_recuperada + self.cantidad_baja
        if total <= 0:
            raise ValidationError(
                "Debes indicar al menos una unidad recuperada o dada de baja."
            )
        if total > mant.cantidad_ingresada:
            raise ValidationError(
                f"La suma de recuperadas ({self.cantidad_recuperada}) + "
                f"bajas ({self.cantidad_baja}) no puede superar las "
                f"ingresadas ({mant.cantidad_ingresada})."
            )

    # El ajuste de stock y el cierre del mantenimiento viven en
    # services.registrar_salida. El modelo solo guarda datos y valida en clean().

    def __str__(self):
        return (
            f"Salida Mant-{self.mantenimiento_id:04d} | "
            f"Recuperadas: {self.cantidad_recuperada} | "
            f"Baja: {self.cantidad_baja}"
        )
