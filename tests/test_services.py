"""The Service model, its factory, and the seed rows it owns.

NOTE: the Django test client is imported as `DjangoClient`, not as `TestClient`, which
pytest would try to collect as a test class. See the note in tests/conftest.py.
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client as DjangoClient

from accounts_receivable.models import Service
from tests.factories.domain import ServiceFactory

pytestmark = pytest.mark.django_db


def seed() -> str:
    """Run the seed command, capturing its output so the test log stays quiet."""
    out = StringIO()
    call_command("seed", stdout=out)

    return out.getvalue()


def test_factory_persists_a_service() -> None:
    programming = ServiceFactory.create_sync()

    assert programming.pk is not None
    assert programming.name
    assert programming.price_cents > 0


def test_service_str_is_its_name() -> None:
    programming = ServiceFactory.create_sync(name="Programming")

    assert str(programming) == "Programming"


def test_seed_creates_the_default_services() -> None:
    seed()

    assert list(Service.objects.values_list("name", "price_cents")) == [
        ("Programming", 8000),
        ("Refactoring", 35000),
    ]


def test_seed_is_idempotent() -> None:
    seed()
    output = seed()

    assert Service.objects.count() == 2
    assert "Service Programming already exists" in output


def test_index_lists_services(client: DjangoClient) -> None:
    ServiceFactory.create_sync(name="Programming", price_cents=8000)

    response = client.get("/services/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Programming" in body
    assert "8000" in body


def test_index_handles_having_no_services(client: DjangoClient) -> None:
    response = client.get("/services/")

    assert response.status_code == 200
    assert b"No services yet" in response.content


def test_detail_shows_one_service(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync(name="Programming")

    response = client.get(f"/services/{programming.pk}/")

    assert response.status_code == 200
    assert b"Programming" in response.content


def test_create_adds_a_service(client: DjangoClient) -> None:
    response = client.post("/services/new/", {"name": "Refactoring", "price_cents": "35000"})

    assert response.status_code == 302
    assert Service.objects.get(name="Refactoring").price_cents == 35000


def test_create_redisplays_an_invalid_form(client: DjangoClient) -> None:
    response = client.post("/services/new/", {"name": "", "price_cents": "abc"})

    assert response.status_code == 200
    assert Service.objects.count() == 0


def test_create_accepts_a_negative_price(client: DjangoClient) -> None:
    """A credit is enterable, as in the Rails source.

    `t.integer` there is signed and the model body is empty, so nothing rejects a
    negative price. Asserted through the form so a later pass does not quietly add a
    validator and call it a bug fix.
    """
    response = client.post("/services/new/", {"name": "Credit", "price_cents": "-8000"})

    assert response.status_code == 302
    assert Service.objects.get(name="Credit").price_cents == -8000


def test_update_edits_a_service(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)

    response = client.post(
        f"/services/{programming.pk}/edit/", {"name": "Programming", "price_cents": "100"}
    )
    programming.refresh_from_db()

    assert response.status_code == 302
    assert programming.price_cents == 100


def test_delete_removes_a_service(client: DjangoClient) -> None:
    programming = ServiceFactory.create_sync()

    response = client.post(f"/services/{programming.pk}/delete/")

    assert response.status_code == 302
    assert Service.objects.count() == 0
