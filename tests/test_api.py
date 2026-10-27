"""Django Ninja is mounted and Pydantic validates responses."""

import platform

import django
import pytest
from django.test import Client

from accounts_receivable.api.schemas import HealthOut, ProductOut, ServiceOut
from tests.factories.domain import ProductFactory, ServiceFactory


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


@pytest.mark.django_db
def test_products_are_listed(client: Client) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software", price_cents=20000)

    response = client.get("/api/products/")

    assert response.status_code == 200
    assert [ProductOut(**row) for row in response.json()] == [
        ProductOut(id=antivirus.pk, name="Anti-virus software", price_cents=20000)
    ]


@pytest.mark.django_db
def test_one_product_is_retrieved(client: Client) -> None:
    antivirus = ProductFactory.create_sync(name="Anti-virus software")

    response = client.get(f"/api/products/{antivirus.pk}")

    assert response.status_code == 200
    assert response.json()["name"] == "Anti-virus software"


@pytest.mark.django_db
def test_an_unknown_product_is_a_404(client: Client) -> None:
    assert client.get("/api/products/999999").status_code == 404


@pytest.mark.django_db
def test_services_are_listed(client: Client) -> None:
    programming = ServiceFactory.create_sync(name="Programming", price_cents=8000)

    response = client.get("/api/services/")

    assert response.status_code == 200
    assert [ServiceOut(**row) for row in response.json()] == [
        ServiceOut(id=programming.pk, name="Programming", price_cents=8000)
    ]


@pytest.mark.django_db
def test_one_service_is_retrieved(client: Client) -> None:
    programming = ServiceFactory.create_sync(name="Programming")

    response = client.get(f"/api/services/{programming.pk}")

    assert response.status_code == 200
    assert response.json()["name"] == "Programming"


@pytest.mark.django_db
def test_an_unknown_service_is_a_404(client: Client) -> None:
    assert client.get("/api/services/999999").status_code == 404
