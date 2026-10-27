from ninja import Schema


class HealthOut(Schema):
    """Response schema for the health endpoint.

    Exists so the Pydantic validation path is genuinely exercised by a request rather
    than merely imported.
    """

    status: str
    django_version: str
    python_version: str


class ProductOut(Schema):
    """Response schema for a product.

    `price_cents` is serialised as the integer it is stored as, matching what the Rails
    views print.
    """

    id: int
    name: str
    price_cents: int


class ServiceOut(Schema):
    """Response schema for a service. Same shape as `ProductOut`, as in the schema."""

    id: int
    name: str
    price_cents: int
