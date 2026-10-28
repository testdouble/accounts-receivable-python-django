"""Read-only endpoints for the two billing tables, invoices and line items.

Read-only for the same reason as `catalog.py`: data entry happens through the app's own
CRUD pages.
"""

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from ninja import Router

from accounts_receivable.api.schemas import InvoiceOut, LineItemOut
from accounts_receivable.models import Invoice, LineItem

invoices_router = Router()
line_items_router = Router()


def _invoices() -> QuerySet[Invoice]:
    """Every invoice with the rows `InvoiceOut.total_cents` needs already loaded."""
    return Invoice.objects.prefetch_related("line_items__product", "line_items__service")


@invoices_router.get("/", response=list[InvoiceOut])
def list_invoices(request) -> list[Invoice]:
    """Every invoice, in the model's `id` order."""
    return list(_invoices())


@invoices_router.get("/{int:invoice_id}", response=InvoiceOut)
def get_invoice(request, invoice_id: int) -> Invoice:
    """One invoice, or a 404 rather than a 500 when the id is unknown."""
    return get_object_or_404(_invoices(), pk=invoice_id)


@line_items_router.get("/", response=list[LineItemOut])
def list_line_items(request) -> list[LineItem]:
    """Every line item, in the model's `id` order."""
    return list(LineItem.objects.select_related("product", "service"))


@line_items_router.get("/{int:line_item_id}", response=LineItemOut)
def get_line_item(request, line_item_id: int) -> LineItem:
    """One line item, or a 404 rather than a 500 when the id is unknown."""
    return get_object_or_404(LineItem.objects.select_related("product", "service"), pk=line_item_id)
