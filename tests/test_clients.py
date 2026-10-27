"""The Client model, its factory, and the seed command.

NOTE: no fixture or local here may be named `client` -- pytest-django reserves that name
for the Django test client. See the note in tests/conftest.py.
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client as DjangoClient

from accounts_receivable.models import Client
from tests.factories.domain import ClientFactory

pytestmark = pytest.mark.django_db


def seed() -> str:
    """Run the seed command, capturing its output so the test log stays quiet."""
    out = StringIO()
    call_command("seed", stdout=out)

    return out.getvalue()


def test_factory_persists_a_client() -> None:
    acme = ClientFactory.create_sync()

    assert acme.pk is not None
    assert acme.name
    assert "@" in acme.email


def test_client_str_is_its_name() -> None:
    acme = ClientFactory.create_sync(name="Acme inc")

    assert str(acme) == "Acme inc"


def test_seed_creates_the_default_clients() -> None:
    seed()

    assert list(Client.objects.values_list("name", "email")) == [
        ("Acme inc", "ap@acme.com"),
        ("Dunder Mifflin", "ap@dundermifflin.com"),
    ]


def test_seed_is_idempotent() -> None:
    seed()
    output = seed()

    assert Client.objects.count() == 2
    assert "already exists" in output


def test_index_lists_clients(client: DjangoClient) -> None:
    ClientFactory.create_sync(name="Acme inc", email="ap@acme.com")

    response = client.get("/clients/")
    body = response.content.decode()

    assert response.status_code == 200
    assert "Acme inc" in body
    assert "ap@acme.com" in body


def test_index_handles_having_no_clients(client: DjangoClient) -> None:
    response = client.get("/clients/")

    assert response.status_code == 200
    assert b"No clients yet" in response.content


def test_detail_shows_one_client(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync(name="Acme inc")

    response = client.get(f"/clients/{acme.pk}/")

    assert response.status_code == 200
    assert b"Acme inc" in response.content


def test_create_adds_a_client(client: DjangoClient) -> None:
    response = client.post(
        "/clients/new/", {"name": "Dunder Mifflin", "email": "ap@dundermifflin.com"}
    )

    assert response.status_code == 302
    assert Client.objects.get(name="Dunder Mifflin").email == "ap@dundermifflin.com"


def test_create_redisplays_an_invalid_form(client: DjangoClient) -> None:
    response = client.post("/clients/new/", {"name": "", "email": "not-an-email"})

    assert response.status_code == 200
    assert Client.objects.count() == 0


def test_update_edits_a_client(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync(name="Acme inc", email="ap@acme.com")

    response = client.post(
        f"/clients/{acme.pk}/edit/", {"name": "Acme inc", "email": "billing@acme.com"}
    )
    acme.refresh_from_db()

    assert response.status_code == 302
    assert acme.email == "billing@acme.com"


def test_delete_removes_a_client(client: DjangoClient) -> None:
    acme = ClientFactory.create_sync()

    response = client.post(f"/clients/{acme.pk}/delete/")

    assert response.status_code == 302
    assert Client.objects.count() == 0
