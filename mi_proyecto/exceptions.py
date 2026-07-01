"""
Manejador de excepciones personalizado para DRF.

Convierte las ValidationError de Django (lanzadas en model.full_clean() /
model.save()) en respuestas HTTP 400 uniformes, en vez de dejar que
escalen a un 500 Internal Server Error.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Traduce la ValidationError de Django a la de DRF (→ 400)
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        else:
            detail = {"detail": exc.messages}
        exc = DRFValidationError(detail)

    return exception_handler(exc, context)
