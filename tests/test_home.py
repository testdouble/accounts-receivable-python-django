"""The root URL and the shared application shell."""

import pytest
from django.test import Client as DjangoClient

pytestmark = pytest.mark.django_db


def test_root_redirects_to_the_clients_index(client: DjangoClient) -> None:
    """The Rails source roots to /invoices; until those exist, clients is the index."""
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/clients/"


def test_the_shell_renders_the_sidebar(client: DjangoClient) -> None:
    response = client.get("/clients/")

    assert response.status_code == 200
    assert "accounts_receivable/base.html" in [t.name for t in response.templates]
    assert "accounts_receivable/_sidebar.html" in [t.name for t in response.templates]
    assert b"<title>Clients</title>" in response.content


def test_the_shell_does_not_leak_its_template_comment(client: DjangoClient) -> None:
    """`{# ... #}` is single-line only, so the old two-line comment was served verbatim."""
    response = client.get("/clients/")

    assert b"Tailwind from the CDN" not in response.content


def test_unbuilt_resources_are_shown_but_not_linked(client: DjangoClient) -> None:
    response = client.get("/clients/")
    body = response.content.decode()

    assert "Invoices" in body
    assert 'href="/invoices' not in body
