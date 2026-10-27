"""Read-only endpoints for the two catalog tables, products and services.

Read-only on purpose: the Rails source has no JSON API at all, so write endpoints would
be invention rather than port. Data entry happens through the app's own CRUD pages.

One module for both routers because the app is organised per layer (`models.py`,
`views.py`, `forms.py`) rather than per resource.
"""

from django.shortcuts import get_object_or_404
from ninja import Router

from accounts_receivable.api.schemas import ProductOut, ServiceOut
from accounts_receivable.models import Product, Service

products_router = Router()
services_router = Router()


@products_router.get("/", response=list[ProductOut])
def list_products(request) -> list[Product]:
    """Every product, in the model's `id` order."""
    return list(Product.objects.all())


@products_router.get("/{int:product_id}", response=ProductOut)
def get_product(request, product_id: int) -> Product:
    """One product, or a 404 rather than a 500 when the id is unknown."""
    return get_object_or_404(Product, pk=product_id)


@services_router.get("/", response=list[ServiceOut])
def list_services(request) -> list[Service]:
    """Every service, in the model's `id` order."""
    return list(Service.objects.all())


@services_router.get("/{int:service_id}", response=ServiceOut)
def get_service(request, service_id: int) -> Service:
    """One service, or a 404 rather than a 500 when the id is unknown."""
    return get_object_or_404(Service, pk=service_id)
