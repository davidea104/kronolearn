"""Health-check endpoint for critical service dependencies."""

from django.db import connection
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    """Report application health without disclosing dependency details."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "degraded"}, status=503)

    return JsonResponse({"status": "ok"})
