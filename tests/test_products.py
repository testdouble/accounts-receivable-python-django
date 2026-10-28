"""The Product model, its factory, and the seed rows it owns.

NOTE: the Django test client is imported as `DjangoClient`, not as `TestClient`, which
pytest would try to collect as a test class. See the note in tests/conftest.py.
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client as DjangoClient

from accounts_receivable.models import Product
from tests.factories.domain import ProductFactory

pytestmark = pytest.mark.django_db


def seed() -> str:
    """Run the seed command, capturing its output so the test log stays quiet."""
    out = StringIO()
    call_command("seed", stdout=out)

    return out.getvalue()


def test_factory_persists_a_product() -> None:
    antivirus = ProductFactory.create_sync()

    assert antivirus.pk is not None
    assert antivirus.name
    assert antivirus.price_cents > 0


def test_product_str_is_its_name() -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software")

    assert str(antivirus) == "Anti-virus software"


def test_seed_creates_the_default_products() -> None:
    seed()

    assert list(Product.objects.values_list("name", "price_cents")) == [
        ("Anti-virus software", 20000),
        ("Serverless servers", 100000),
    ]


def test_seed_is_idempotent() -> None:
    seed()
    output = seed()

    assert Product.objects.count() == 2
    assert "Product Anti-virus software already exists" in output


def test_index_lists_products(client: DjangoClient) -> None:
    ProductFactory.create_sync(name="Anti-virus software", price_cents=20000)

    response = client.get("/products/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Anti-virus software" in body
    assert "20000" in body


def test_index_handles_having_no_products(client: DjangoClient) -> None:
    response = client.get("/products/")

    assert response.status_code == 200
    assert b"No products yet" in response.content


def test_detail_shows_one_product(client: DjangoClient) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software")

    response = client.get(f"/products/{antivirus.pk}/")

    assert response.status_code == 200
    assert b"Anti-virus software" in response.content


def test_create_adds_a_product(client: DjangoClient) -> None:
    response = client.post(
        "/products/new/", {"name": "Serverless servers", "price_cents": "100000"}
    )

    assert response.status_code == 302
    assert Product.objects.get(name="Serverless servers").price_cents == 100000


def test_create_redisplays_an_invalid_form(client: DjangoClient) -> None:
    response = client.post("/products/new/", {"name": "", "price_cents": "abc"})

    assert response.status_code == 200
    assert Product.objects.count() == 0


def test_create_accepts_a_negative_price(client: DjangoClient) -> None:
    """A credit is enterable: nothing rejects a negative price."""
    response = client.post("/products/new/", {"name": "Credit", "price_cents": "-20000"})

    assert response.status_code == 302
    assert Product.objects.get(name="Credit").price_cents == -20000


def test_update_edits_a_product(client: DjangoClient) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software", price_cents=20000)

    response = client.post(
        f"/products/{antivirus.pk}/edit/", {"name": "Anti-virus software", "price_cents": "100"}
    )
    antivirus.refresh_from_db()

    assert response.status_code == 302
    assert antivirus.price_cents == 100


def test_delete_removes_a_product(client: DjangoClient) -> None:
    antivirus = ProductFactory.create_sync()

    response = client.post(f"/products/{antivirus.pk}/delete/")

    assert response.status_code == 302
    assert Product.objects.count() == 0
