"""The Invoice model, its CRUD pages, and the invoice show page's money arithmetic.

NOTE: the Django test client is imported as `DjangoClient`, not as `TestClient`, which
pytest would try to collect as a test class, and the domain's `Client` is never bound to
a fixture named `client`. See the note in tests/conftest.py.
"""

import datetime as dt
from io import StringIO

import pytest
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import Client as DjangoClient

from accounts_receivable.models import Invoice, LineItem
from tests.factories.domain import (
    ClientFactory,
    InvoiceFactory,
    LineItemFactory,
    ProductFactory,
    ServiceFactory,
)

pytestmark = pytest.mark.django_db


def seed() -> str:
    """Run the seed command, capturing its output so the test log stays quiet."""
    out = StringIO()
    call_command("seed", stdout=out)

    return out.getvalue()


def test_factory_persists_an_invoice() -> None:
    invoice = InvoiceFactory.create_sync()

    assert invoice.pk is not None
    assert invoice.client_id is not None
    assert invoice.net_days == 30


def test_invoice_str_is_its_number() -> None:
    invoice = InvoiceFactory.create_sync()

    assert str(invoice) == f"Invoice #{invoice.pk}"


def test_net_days_defaults_to_thirty() -> None:
    acme = ClientFactory.create_sync()
    invoice = Invoice.objects.create(client=acme)

    assert invoice.net_days == 30


def test_due_date_is_net_days_after_creation() -> None:
    invoice = InvoiceFactory.create_sync(net_days=45)

    assert invoice.due_date == invoice.created_at.date() + dt.timedelta(days=45)


def test_due_date_is_none_before_the_row_is_saved() -> None:
    """`auto_now_add` has not run yet, so there is no issue date to count from."""
    assert Invoice(net_days=30).due_date is None


def test_total_cents_sums_every_line_item() -> None:
    invoice = InvoiceFactory.create_sync()
    programming = ServiceFactory.create_sync(price_cents=8000)
    servers = ProductFactory.create_sync(price_cents=100000)
    LineItemFactory.create_sync(invoice=invoice, service=programming, quantity=40)
    LineItemFactory.create_sync(invoice=invoice, product=servers, quantity=2)

    assert invoice.total_cents == 520000


def test_total_cents_counts_a_zero_priced_line_item_the_page_would_drop() -> None:
    invoice = InvoiceFactory.create_sync()
    freebie = ProductFactory.create_sync(price_cents=0)
    LineItemFactory.create_sync(
        invoice=invoice, product=freebie, price_override_cents=50000, quantity=1
    )

    assert invoice.total_cents == 50000


def test_total_cents_is_zero_for_an_empty_invoice() -> None:
    assert InvoiceFactory.create_sync().total_cents == 0


def test_deleting_an_invoice_deletes_its_line_items() -> None:
    invoice = InvoiceFactory.create_sync()
    LineItemFactory.create_sync(invoice=invoice, product=ProductFactory.create_sync())

    invoice.delete()

    assert LineItem.objects.count() == 0


def test_deleting_an_invoiced_client_is_refused() -> None:
    acme = ClientFactory.create_sync()
    InvoiceFactory.create_sync(client=acme)

    with pytest.raises(ProtectedError):
        acme.delete()


def test_seed_creates_the_default_invoices() -> None:
    seed()

    assert list(Invoice.objects.values_list("client__name", "net_days", "note")) == [
        ("Acme inc", 30, "Invoice for writing software for Acme"),
        ("Acme inc", 30, "Invoice for refactoring software for Acme"),
    ]


def test_seed_is_idempotent() -> None:
    seed()
    output = seed()

    assert Invoice.objects.count() == 2
    assert "Invoice Invoice for writing software for Acme already exists" in output


def test_index_lists_invoices(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync(name="Acme inc")
    InvoiceFactory.create_sync(client=acme, note="Invoice for writing software for Acme")

    response = client.get("/invoices/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Acme inc" in body
    assert "Invoice for writing software for Acme" in body


def test_index_handles_having_no_invoices(client: DjangoClient) -> None:
    response = client.get("/invoices/")

    assert response.status_code == 200
    assert b"No invoices yet" in response.content


def test_detail_shows_the_client_and_the_due_date(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync(name="Acme inc", email="ap@acme.com")
    invoice = InvoiceFactory.create_sync(client=acme, net_days=30)

    response = client.get(f"/invoices/{invoice.pk}/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Acme inc" in body
    assert "ap@acme.com" in body
    assert invoice.due_date.isoformat() in body


def test_detail_handles_an_invoice_with_no_line_items(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()

    response = client.get(f"/invoices/{invoice.pk}/")

    assert response.status_code == 200
    assert b"Nothing billed yet" in response.content


def test_detail_totals_products_and_services_together(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)
    servers = ProductFactory.create_sync(name="Serverless servers", price_cents=100000)
    LineItemFactory.create_sync(invoice=invoice, service=programming, quantity=40)
    LineItemFactory.create_sync(invoice=invoice, product=servers, quantity=2)

    response = client.get(f"/invoices/{invoice.pk}/")

    assert response.status_code == 200
    # 40 * 8000 + 2 * 100000 = 520000.
    assert response.context["total_cents"] == 520000
    assert b"$5200.00" in response.content


def test_detail_prefers_the_override_to_the_catalog_price(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)
    LineItemFactory.create_sync(
        invoice=invoice, service=programming, price_override_cents=4000, quantity=40
    )

    response = client.get(f"/invoices/{invoice.pk}/")
    body = response.content.decode()

    assert response.context["total_cents"] == 160000
    assert "$40.00" in body
    assert "$80.00" not in body


def test_detail_drops_a_line_item_priced_from_a_zero_cost_catalog_row(
    client: DjangoClient,
) -> None:
    invoice = InvoiceFactory.create_sync()
    freebie = ProductFactory.create_sync(name="Complimentary onboarding", price_cents=0)
    LineItemFactory.create_sync(
        invoice=invoice,
        product=freebie,
        price_override_cents=50000,
        quantity=1,
        description="Billed onboarding",
    )

    response = client.get(f"/invoices/{invoice.pk}/")
    body = response.content.decode()

    assert response.context["total_cents"] == 0
    assert "Complimentary onboarding" not in body
    assert "Billed onboarding" not in body


def test_detail_breaks_on_a_line_item_priced_under_a_dime(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()
    cheap = ServiceFactory.create_sync(price_cents=5)
    LineItemFactory.create_sync(invoice=invoice, service=cheap, quantity=1)

    with pytest.raises(IndexError):
        client.get(f"/invoices/{invoice.pk}/")


def test_create_adds_an_invoice(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync()

    response = client.post(
        "/invoices/new/",
        {"client": str(acme.pk), "net_days": "30", "note": "Invoice for writing software"},
    )

    assert response.status_code == 302
    assert Invoice.objects.get(note="Invoice for writing software").client_id == acme.pk


def test_create_redisplays_an_invalid_form(client: DjangoClient) -> None:
    response = client.post("/invoices/new/", {"client": "", "net_days": "abc"})

    assert response.status_code == 200
    assert Invoice.objects.count() == 0


def test_update_edits_an_invoice(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync(net_days=30)
    other = ClientFactory.create_sync()

    response = client.post(
        f"/invoices/{invoice.pk}/edit/",
        {"client": str(other.pk), "net_days": "60", "note": invoice.note},
    )
    invoice.refresh_from_db()

    assert response.status_code == 302
    assert invoice.client_id == other.pk
    assert invoice.net_days == 60


def test_delete_removes_an_invoice_and_its_line_items(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()
    LineItemFactory.create_sync(invoice=invoice, service=ServiceFactory.create_sync())

    response = client.post(f"/invoices/{invoice.pk}/delete/")

    assert response.status_code == 302
    assert Invoice.objects.count() == 0
    assert LineItem.objects.count() == 0
