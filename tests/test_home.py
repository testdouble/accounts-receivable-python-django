"""The Django Template Language layer renders."""

from django.test import Client


def test_home_renders(client: Client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "accounts_receivable/home.html" in [t.name for t in response.templates]


def test_home_extends_the_base_layout(client: Client) -> None:
    response = client.get("/")

    assert "accounts_receivable/base.html" in [t.name for t in response.templates]
    assert b"<title>AccountsReceivable</title>" in response.content
