"""Django Ninja is mounted and Pydantic validates responses."""

import platform

import django
import pytest
from django.test import Client

from accounts_receivable.api.schemas import (
    HealthOut,
    InvoiceOut,
    LineItemOut,
    ProductOut,
    ServiceOut,
)
from tests.factories.domain import (
    ClientFactory,
    InvoiceFactory,
    LineItemFactory,
    ProductFactory,
    ServiceFactory,
)


def test_health_returns_a_schema_valid_body(client: Client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    # Round-tripping through the schema is the actual assertion: it fails if the
    # endpoint drops a field or changes a type.
    body = HealthOut(**response.json())
    assert body.status == "ok"
    assert body.django_version == django.get_version()
    assert body.python_version == platform.python_version()


def test_openapi_schema_is_served(client: Client) -> None:
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/api/health" in schema["paths"]


def test_docs_are_served(client: Client) -> None:
    assert client.get("/api/docs").status_code == 200


@pytest.mark.django_db
def test_products_are_listed(client: Client) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software", price_cents=20000)

    response = client.get("/api/products/")

    assert response.status_code == 200
    assert [ProductOut(**row) for row in response.json()] == [
        ProductOut(id=antivirus.pk, name="Anti-virus software", price_cents=20000)
    ]


@pytest.mark.django_db
def test_one_product_is_retrieved(client: Client) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software")

    response = client.get(f"/api/products/{antivirus.pk}")

    assert response.status_code == 200
    assert response.json()["name"] == "Anti-virus software"


@pytest.mark.django_db
def test_an_unknown_product_is_a_404(client: Client) -> None:
    assert client.get("/api/products/999999").status_code == 404


@pytest.mark.django_db
def test_services_are_listed(client: Client) -> None:
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)

    response = client.get("/api/services/")

    assert response.status_code == 200
    assert [ServiceOut(**row) for row in response.json()] == [
        ServiceOut(id=programming.pk, name="Programming", price_cents=8000)
    ]


@pytest.mark.django_db
def test_one_service_is_retrieved(client: Client) -> None:
    programming = ServiceFactory.create_sync(name="Programming")

    response = client.get(f"/api/services/{programming.pk}")

    assert response.status_code == 200
    assert response.json()["name"] == "Programming"


@pytest.mark.django_db
def test_an_unknown_service_is_a_404(client: Client) -> None:
    assert client.get("/api/services/999999").status_code == 404


@pytest.mark.django_db
def test_invoices_are_listed(client: Client) -> None:
    acme = ClientFactory.create_sync()
    invoice = InvoiceFactory.create_sync(client=acme, net_days=30, note="Invoice for Acme")
    programming = ServiceFactory.create_sync(price_cents=8000)
    LineItemFactory.create_sync(invoice=invoice, service=programming, quantity=40)

    response = client.get("/api/invoices/")

    assert response.status_code == 200
    assert [InvoiceOut(**row) for row in response.json()] == [
        InvoiceOut(
            id=invoice.pk,
            client_id=acme.pk,
            net_days=30,
            note="Invoice for Acme",
            due_date=invoice.due_date,
            total_cents=320000,
        )
    ]


@pytest.mark.django_db
def test_one_invoice_is_retrieved(client: Client) -> None:
    invoice = InvoiceFactory.create_sync(note="Invoice for Acme")

    response = client.get(f"/api/invoices/{invoice.pk}")

    assert response.status_code == 200
    assert response.json()["note"] == "Invoice for Acme"


@pytest.mark.django_db
def test_an_invoice_total_counts_a_zero_priced_line_item(client: Client) -> None:
    invoice = InvoiceFactory.create_sync()
    freebie = ProductFactory.create_sync(price_cents=0)
    LineItemFactory.create_sync(
        invoice=invoice, product=freebie, price_override_cents=50000, quantity=1
    )

    response = client.get(f"/api/invoices/{invoice.pk}")

    assert response.json()["total_cents"] == 50000
    assert client.get(f"/invoices/{invoice.pk}/").context["total_cents"] == 0


@pytest.mark.django_db
def test_an_unknown_invoice_is_a_404(client: Client) -> None:
    assert client.get("/api/invoices/999999").status_code == 404


@pytest.mark.django_db
def test_line_items_are_listed(client: Client) -> None:
    programming = ServiceFactory.create_sync(price_cents=8000)
    item = LineItemFactory.create_sync(
        service=programming,
        price_override_cents=4000,
        quantity=40,
        description="Justin's discount programming",
    )

    response = client.get("/api/line-items/")

    assert response.status_code == 200
    assert [LineItemOut(**row) for row in response.json()] == [
        LineItemOut(
            id=item.pk,
            invoice_id=item.invoice_id,
            product_id=None,
            service_id=programming.pk,
            price_override_cents=4000,
            quantity=40,
            description="Justin's discount programming",
            unit_price_cents=4000,
            subtotal_cents=160000,
        )
    ]


@pytest.mark.django_db
def test_a_line_item_without_an_override_is_priced_from_its_catalog_row(client: Client) -> None:
    antivirus = ProductFactory.create_sync(price_cents=20000)
    item = LineItemFactory.create_sync(product=antivirus, quantity=2)

    response = client.get(f"/api/line-items/{item.pk}")
    body = response.json()

    assert response.status_code == 200
    assert body["price_override_cents"] is None
    assert body["unit_price_cents"] == 20000
    assert body["subtotal_cents"] == 40000


@pytest.mark.django_db
def test_an_unknown_line_item_is_a_404(client: Client) -> None:
    assert client.get("/api/line-items/999999").status_code == 404
