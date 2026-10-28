"""The root URL and the shared application shell."""

import pytest
from django.test import Client as DjangoClient

pytestmark = pytest.mark.django_db


def test_root_redirects_to_the_invoices_index(client: DjangoClient) -> None:
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/invoices/"


def test_the_shell_renders_the_sidebar(client: DjangoClient) -> None:
    response = client.get("/clients/")

    assert response.status_code == 200
    assert "accounts_receivable/base.html" in [t.name for t in response.templates]
    assert "accounts_receivable/_sidebar.html" in [t.name for t in response.templates]
    assert b"<title>Clients</title>" in response.content


def test_the_shell_does_not_leak_its_template_comment(client: DjangoClient) -> None:
    """`{# ... #}` is single-line only; a multi-line comment needs `{% comment %}`."""
    response = client.get("/clients/")

    assert b"Tailwind from the CDN" not in response.content


def test_every_resource_is_linked(client: DjangoClient) -> None:
    """Every resource in the domain is built, so no nav item is a muted placeholder."""
    response = client.get("/clients/")
    body = response.content.decode()

    assert 'href="/clients/"' in body
    assert 'href="/products/"' in body
    assert 'href="/services/"' in body
    assert 'href="/invoices/"' in body
    assert 'href="/line_items/"' in body
