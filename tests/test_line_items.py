"""The LineItem model, its product-or-service rule, its pricing, and its CRUD pages.

NOTE: the Django test client is imported as `DjangoClient`, not as `TestClient`, which
pytest would try to collect as a test class. See the note in tests/conftest.py.
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client as DjangoClient
from django.utils.html import escape

from accounts_receivable.forms import LineItemForm
from accounts_receivable.models import LineItem
from tests.factories.domain import (
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


def test_factory_persists_a_line_item() -> None:
    item = LineItemFactory.create_sync(product=ProductFactory.create_sync())

    assert item.pk is not None
    assert item.invoice_id is not None
    assert 1 <= item.quantity <= 40


def test_quantity_defaults_to_one() -> None:
    item = LineItem.objects.create(
        invoice=InvoiceFactory.create_sync(), product=ProductFactory.create_sync()
    )

    assert item.quantity == 1


def test_str_is_the_description() -> None:
    item = LineItemFactory.create_sync(description="Amber's quality programming")

    assert str(item) == "Amber's quality programming"


def test_str_falls_back_to_the_number_when_there_is_no_description() -> None:
    item = LineItemFactory.create_sync(description="")

    assert str(item) == f"Line item #{item.pk}"


def test_unit_price_comes_from_the_product() -> None:
    antivirus = ProductFactory.create_sync(price_cents=20000)
    item = LineItemFactory.create_sync(product=antivirus)

    assert item.unit_price_cents == 20000


def test_unit_price_comes_from_the_service() -> None:
    programming = ServiceFactory.create_sync(price_cents=8000)
    item = LineItemFactory.create_sync(service=programming)

    assert item.unit_price_cents == 8000


def test_an_override_beats_the_catalog_price() -> None:
    programming = ServiceFactory.create_sync(price_cents=8000)
    item = LineItemFactory.create_sync(service=programming, price_override_cents=4000)

    assert item.unit_price_cents == 4000


def test_an_override_of_zero_is_honoured() -> None:
    """A free line, not a missing override.

    `unit_price_cents` tests `is not None` rather than truthiness, so an override of 0
    is honoured instead of falling through to the catalog price.
    """
    programming = ServiceFactory.create_sync(price_cents=8000)
    item = LineItemFactory.create_sync(service=programming, price_override_cents=0)

    assert item.unit_price_cents == 0
    assert item.subtotal_cents == 0


def test_subtotal_is_the_unit_price_times_the_quantity() -> None:
    programming = ServiceFactory.create_sync(price_cents=8000)
    item = LineItemFactory.create_sync(service=programming, quantity=40)

    assert item.subtotal_cents == 320000


def test_pricing_is_none_without_a_product_or_a_service() -> None:
    """Reachable only through the ORM, which does not run `clean()`."""
    item = LineItemFactory.create_sync()

    assert item.unit_price_cents is None
    assert item.subtotal_cents is None


def _form_data(**overrides: object) -> dict[str, object]:
    data = {
        "invoice": str(InvoiceFactory.create_sync().pk),
        "product": "",
        "service": "",
        "price_override_cents": "",
        "quantity": "1",
        "description": "Amber's quality programming",
    }

    return {**data, **overrides}


def test_a_product_alone_is_valid() -> None:
    form = LineItemForm(_form_data(product=str(ProductFactory.create_sync().pk)))

    assert form.is_valid(), form.errors


def test_a_service_alone_is_valid() -> None:
    form = LineItemForm(_form_data(service=str(ServiceFactory.create_sync().pk)))

    assert form.is_valid(), form.errors


def test_neither_a_product_nor_a_service_is_invalid() -> None:
    form = LineItemForm(_form_data())

    assert not form.is_valid()
    assert "A line item must be either a product or a service" in form.non_field_errors()


def test_both_a_product_and_a_service_is_invalid() -> None:
    form = LineItemForm(
        _form_data(
            product=str(ProductFactory.create_sync().pk),
            service=str(ServiceFactory.create_sync().pk),
        )
    )

    assert not form.is_valid()
    assert "A line item can't be both a product and a service" in form.non_field_errors()


def test_seed_creates_the_default_line_items() -> None:
    seed()

    assert list(
        LineItem.objects.values_list(
            "product__name", "service__name", "price_override_cents", "quantity", "description"
        )
    ) == [
        (None, "Programming", None, 40, "Amber's quality programming"),
        (None, "Programming", 4000, 40, "Justin's discount programming"),
        (
            "Serverless servers",
            None,
            None,
            20,
            "Enough serverless hardware to achieve web-scale",
        ),
        (None, "Refactoring", None, 40, "Megan fixing previous discount programming"),
        ("Anti-virus software", None, None, 1, "Anti-virus software subscription"),
    ]


def test_seed_is_idempotent() -> None:
    seed()
    output = seed()

    assert LineItem.objects.count() == 5
    assert "Line item Amber's quality programming already exists" in output


def test_index_lists_line_items(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync(name="Programming")
    LineItemFactory.create_sync(
        service=programming, quantity=40, description="Amber's quality programming"
    )

    response = client.get("/line_items/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Programming" in body
    # `escape`, because the DTL autoescapes the apostrophe in the seed's own wording.
    assert escape("Amber's quality programming") in body


def test_index_handles_having_no_line_items(client: DjangoClient) -> None:
    response = client.get("/line_items/")

    assert response.status_code == 200
    assert b"No line items yet" in response.content


def test_detail_shows_one_line_item(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)
    item = LineItemFactory.create_sync(
        service=programming, quantity=40, description="Amber's quality programming"
    )

    response = client.get(f"/line_items/{item.pk}/")
    body = response.content.decode()

    assert response.status_code == 200
    assert escape("Amber's quality programming") in body
    assert "$80.00" in body
    assert "$3200.00" in body


def test_create_adds_a_line_item(client: DjangoClient) -> None:
    invoice = InvoiceFactory.create_sync()
    programming = ServiceFactory.create_sync()

    response = client.post(
        "/line_items/new/",
        _form_data(
            invoice=str(invoice.pk),
            service=str(programming.pk),
            quantity="40",
            description="Amber's quality programming",
        ),
    )

    assert response.status_code == 302
    created = LineItem.objects.get(description="Amber's quality programming")
    assert created.service_id == programming.pk
    assert created.quantity == 40


def test_create_leaves_a_blank_override_null(client: DjangoClient) -> None:
    """Blank means "charge the catalog price", which is NULL rather than 0."""
    response = client.post(
        "/line_items/new/", _form_data(product=str(ProductFactory.create_sync().pk))
    )

    assert response.status_code == 302
    assert LineItem.objects.get().price_override_cents is None


def test_create_redisplays_a_line_item_with_neither_a_product_nor_a_service(
    client: DjangoClient,
) -> None:
    response = client.post("/line_items/new/", _form_data())
    body = response.content.decode()

    assert response.status_code == 200
    assert LineItem.objects.count() == 0
    assert "A line item must be either a product or a service" in body


def test_update_edits_a_line_item(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync()
    item = LineItemFactory.create_sync(service=programming, quantity=40)
    refactoring = ServiceFactory.create_sync()

    response = client.post(
        f"/line_items/{item.pk}/edit/",
        _form_data(
            invoice=str(item.invoice_id),
            service=str(refactoring.pk),
            price_override_cents="4000",
            quantity="10",
            description=item.description,
        ),
    )
    item.refresh_from_db()

    assert response.status_code == 302
    assert item.service_id == refactoring.pk
    assert item.price_override_cents == 4000
    assert item.quantity == 10


def test_delete_removes_a_line_item(client: DjangoClient) -> None:
    item = LineItemFactory.create_sync(product=ProductFactory.create_sync())

    response = client.post(f"/line_items/{item.pk}/delete/")

    assert response.status_code == 302
    assert LineItem.objects.count() == 0
