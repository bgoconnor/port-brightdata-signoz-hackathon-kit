from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    del request
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {
                "status": "error",
                "service": "paper-factory-backend",
                "environment": settings.ENVIRONMENT,
                "database": "unavailable",
            },
            status=503,
        )

    return JsonResponse(
        {
            "status": "ok",
            "service": "paper-factory-backend",
            "environment": settings.ENVIRONMENT,
            "database": "ok",
        }
    )

