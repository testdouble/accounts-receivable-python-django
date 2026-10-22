from ninja import Schema


class HealthOut(Schema):
    """Response schema for the health endpoint.

    Exists so the Pydantic validation path is genuinely exercised by a request rather
    than merely imported.
    """

    status: str
    django_version: str
    python_version: str
