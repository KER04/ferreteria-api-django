"""
Health check para monitoreo y orquestadores (Docker, Kubernetes, Render...).
Verifica que la app responde y que la base de datos está accesible.
"""
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []          # no requiere token

    @extend_schema(
        responses=inline_serializer("HealthResponse", {
            "status":   serializers.CharField(),
            "database": serializers.BooleanField(),
        }),
        summary="Estado del servicio",
    )
    def get(self, request):
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        return Response(
            {"status": "ok" if db_ok else "error", "database": db_ok},
            status=200 if db_ok else 503,
        )
