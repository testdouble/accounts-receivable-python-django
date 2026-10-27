"""The Client model, its factory, and the seed command.

NOTE: no fixture or local here may be named `client` -- pytest-django reserves that name
for the Django test client. See the note in tests/conftest.py.
"""

from io import StringIO

import pytest
from django.core.management import call_command

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
