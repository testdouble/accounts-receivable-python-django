import datetime as dt

from ninja import Schema


class HealthOut(Schema):
    """Response schema for the health endpoint.

    Exists so the Pydantic validation path is genuinely exercised by a request rather
    than merely imported.
    """

    status: str
    django_version: str
    python_version: str


class ProductOut(Schema):
    """Response schema for a product.

    `price_cents` is serialised as the integer it is stored as, matching what the Rails
    views print.
    """

    id: int
    name: str
    price_cents: int


class ServiceOut(Schema):
    """Response schema for a service. Same shape as `ProductOut`, as in the schema."""

    id: int
    name: str
    price_cents: int


class InvoiceOut(Schema):
    """Response schema for an invoice.

    `subject` and `issue_date` are not columns: the Rails schema has `note` and
    `created_at`, and this serialises what is stored. `due_date` and `total_cents` are
    derived, and are the two values a consumer would otherwise have to recompute.

    NOTE: `total_cents` is `Invoice.total_cents`, the honest sum of every line item. The
    invoice *page* can print less, because `InvoiceDetailView` preserves the Rails defect
    that drops line items priced from a zero-cost product or service. The API has no
    Rails counterpart to be faithful to, so it does not reproduce that filter.
    """

    id: int
    client_id: int
    net_days: int
    note: str
    due_date: dt.date
    total_cents: int


class LineItemOut(Schema):
    """Response schema for a line item.

    `product_id` and `service_id` are mutually exclusive; exactly one is set.
    `unit_price_cents` is the override when there is one and the catalog price otherwise,
    so a consumer does not have to re-derive the fallback -- including the easily-missed
    case of an override of 0.
    """

    id: int
    invoice_id: int
    product_id: int | None
    service_id: int | None
    price_override_cents: int | None
    quantity: int
    description: str
    unit_price_cents: int
    subtotal_cents: int
