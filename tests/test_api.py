"""Django Ninja is mounted and Pydantic validates responses."""

import platform

import django
from django.test import Client

from accounts_receivable.api.schemas import HealthOut


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
