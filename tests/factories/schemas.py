"""Factories for Pydantic schemas.

This is the clean contrast with `tests/factories/base.py`: PolyFactory supports
Pydantic natively, so API schemas need no adapter at all. Only Django ORM models do.
"""

from polyfactory.factories.pydantic_factory import ModelFactory

from accounts_receivable.api.schemas import HealthOut


class HealthOutFactory(ModelFactory[HealthOut]):
    __model__ = HealthOut
    __allow_none_optionals__ = False
