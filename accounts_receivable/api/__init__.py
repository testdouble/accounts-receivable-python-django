"""Django Ninja API.

Note: `NinjaAPI` is unauthenticated and CSRF-exempt by default. That is correct for a
port of an application with no users, but it is a deliberate choice rather than an
oversight.
"""

import platform

import django
from ninja import NinjaAPI

from accounts_receivable.api.schemas import HealthOut

api = NinjaAPI(title="Accounts Receivable", version="0.1.0")


@api.get("/health", response=HealthOut, tags=["meta"])
def health(request) -> HealthOut:
    """Report that the stack is wired up, and what it is running on."""
    return HealthOut(
        status="ok",
        django_version=django.get_version(),
        python_version=platform.python_version(),
    )
