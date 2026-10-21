"""PolyFactory's native Pydantic support needs no adapter."""

from accounts_receivable.api.schemas import HealthOut
from tests.factories.schemas import HealthOutFactory


def test_builds_a_valid_schema_instance() -> None:
    built = HealthOutFactory.build()

    assert isinstance(built, HealthOut)
    assert isinstance(built.status, str)
    assert isinstance(built.django_version, str)
    assert isinstance(built.python_version, str)


def test_caller_kwargs_win_over_generated_values() -> None:
    assert HealthOutFactory.build(status="degraded").status == "degraded"
