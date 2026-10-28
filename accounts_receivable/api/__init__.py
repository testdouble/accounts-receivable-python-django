"""Django Ninja API.

`NinjaAPI` is unauthenticated and CSRF-exempt by default, which is correct for an
application with no users.
"""

import platform

import django
from ninja import NinjaAPI

from accounts_receivable.api.billing import invoices_router, line_items_router
from accounts_receivable.api.catalog import products_router, services_router
from accounts_receivable.api.schemas import HealthOut

api = NinjaAPI(title="Accounts Receivable", version="0.1.0")
api.add_router("/products", products_router, tags=["products"])
api.add_router("/services", services_router, tags=["services"])
api.add_router("/invoices", invoices_router, tags=["invoices"])
api.add_router("/line-items", line_items_router, tags=["line items"])


@api.get("/health", response=HealthOut, tags=["meta"])
def health(request) -> HealthOut:
    """Report that the stack is wired up, and what it is running on."""
    return HealthOut(
        status="ok",
        django_version=django.get_version(),
        python_version=platform.python_version(),
    )
