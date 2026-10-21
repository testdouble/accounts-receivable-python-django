"""A Django adapter for PolyFactory.

PolyFactory 3.5.0 ships support for Pydantic, attrs, msgspec, beanie, odmantic and
SQLAlchemy -- and *no* Django support. There is no `DjangoModelFactory`, so it cannot
fill the FactoryBot role for Django ORM models as shipped. `BaseFactory` only declares
two abstract methods, though, so the adapter is small; `get_model_fields()` is where
all the real work lives.

Known deviations from FactoryBot, all deliberate:

* Associations declared as `Use(ParentFactory.create_sync)` are **persisted even when
  you call `.build()`**. Django needs a saved target for a ForeignKey to be usable, so
  this is the right trade -- but it is not FactoryBot's semantics and it will surprise
  someone. Pass an instance yourself to avoid it.
* **No reverse-relation support.** FactoryBot's `create(:invoice, line_items: [...])`
  has no equivalent: `get_model_fields` filters to `models.Field`, which excludes
  reverse descriptors. Build multi-object graphs with plain ORM helpers instead.
* **No `sequence` equivalent.** PolyFactory v3 removed `Fixture` and has no counter, so
  uniqueness relies on Faker's randomness. A `UniqueConstraint` would need a
  hand-rolled counter.
* `__check_model__` defaults to True in v3, so declared fields must match model field
  names exactly -- `author`, not `author_id`.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, get_args
from uuid import UUID

from django.db import models
from polyfactory.factories.base import BaseFactory
from polyfactory.field_meta import Constraints, FieldMeta, Null

if TYPE_CHECKING:
    from typing import TypeGuard

#: Django field class -> Python annotation. Resolved by walking the field's MRO, so
#: EmailField/SlugField/URLField fall through to CharField -> str, and a custom field
#: falls back to whichever built-in it subclasses.
#:
#: Order matters: DateTimeField MUST precede DateField because it subclasses it.
#: Reordering this dict silently produces `date` objects for datetime columns.
FIELD_TYPE_MAP: dict[type[models.Field], Any] = {
    models.BinaryField: bytes,
    models.BooleanField: bool,
    models.DateTimeField: dt.datetime,
    models.DateField: dt.date,
    models.DecimalField: Decimal,
    models.DurationField: dt.timedelta,
    models.FloatField: float,
    models.IntegerField: int,
    models.JSONField: dict,
    models.TimeField: dt.time,
    models.UUIDField: UUID,
    models.CharField: str,
    models.TextField: str,
}


class DjangoSyncPersistence[T: models.Model]:
    """Implements PolyFactory's `SyncPersistenceProtocol` against the Django ORM."""

    def save(self, data: T) -> T:
        # `force_insert=True` makes this semantically identical to `objects.create()`
        # (guaranteed INSERT, no silent UPDATE on a pk collision). We save the instance
        # PolyFactory already built rather than round-tripping back through kwargs,
        # which would lose related objects.
        data.save(force_insert=True)
        return data

    def save_many(self, data: list[T]) -> list[T]:
        # Deliberately not `bulk_create`: it skips `save()` overrides and, on some
        # backends, primary-key backfill. Correctness over speed.
        for instance in data:
            instance.save(force_insert=True)
        return data


class DjangoModelFactory[T: models.Model](BaseFactory[T]):
    """Base factory for Django models."""

    __is_base_factory__ = True
    __sync_persistence__ = DjangoSyncPersistence
    # PolyFactory defaults this to True, which sets nullable fields to None about half
    # the time. Tests need determinism.
    __allow_none_optionals__ = False

    #: Generate a value for the primary key. Almost never what you want -- leaving it
    #: unset is what makes `create_sync()` perform a real INSERT.
    __set_primary_key__: ClassVar[bool] = False

    #: Auto-resolve ForeignKeys through related factories. OFF by default: a model with
    #: two mutually-exclusive nullable FKs (the shape the real `LineItem` has) would get
    #: both populated on every build, violating its own XOR rule 100% of the time. There
    #: is no per-field way to express "fill this FK, leave that one alone" through a
    #: single flag, so declare associations explicitly with `Use(...)` instead.
    __set_foreign_keys__: ClassVar[bool] = False

    __config_keys__ = (
        *BaseFactory.__config_keys__,
        "__set_primary_key__",
        "__set_foreign_keys__",
    )

    # ---- abstract method 1 of 2 ----
    @classmethod
    def is_supported_type(cls, value: Any) -> TypeGuard[type[T]]:
        return isinstance(value, type) and issubclass(value, models.Model)

    # ---- abstract method 2 of 2: all the real work ----
    @classmethod
    def get_model_fields(cls) -> list[FieldMeta]:
        fields: list[FieldMeta] = []

        for field in cls.__model__._meta.get_fields():
            if not isinstance(field, models.Field):
                continue  # reverse relations, GenericForeignKey
            if field.primary_key and not cls.__set_primary_key__:
                continue
            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                continue  # created_at / updated_at: the ORM owns these
            if not field.editable:
                continue  # AutoField and friends

            # Relation fields are always listed, even when __set_foreign_keys__ is
            # False: PolyFactory's __check_model__ validates declared factory
            # attributes against this list, so omitting them would make
            # `author = Use(AuthorFactory.create_sync)` a configuration error.
            # Whether a value gets *generated* is decided in should_set_field_value().
            if field.is_relation:
                annotation: Any = field.related_model
            else:
                annotation = cls.annotation_for_field(field)

            if field.null:
                annotation = annotation | None

            fields.append(
                FieldMeta.from_type(
                    annotation=annotation,
                    # `field.name` not `field.attname`: FK -> "author", not "author_id".
                    # Model(author=obj) is what we want to pass.
                    name=field.name,
                    default=field.default if field.has_default() else Null,
                    constraints=cls.constraints_for_field(field),
                    # Always required, even for nullable columns. PolyFactory skips
                    # non-required fields at random (base.py: `if not
                    # field_meta.required and create_random_boolean(...)`), which is
                    # independent of __allow_none_optionals__ and would make generation
                    # nondeterministic. Declare `= None` on a factory to get a null.
                    required=True,
                )
            )

        return fields

    @classmethod
    def annotation_for_field(cls, field: models.Field) -> Any:
        for klass in type(field).__mro__:
            if klass in FIELD_TYPE_MAP:
                return FIELD_TYPE_MAP[klass]
        msg = (
            f"{cls.__name__}: no type mapping for {type(field).__name__} "
            f"(field {field.name!r}). Add it to FIELD_TYPE_MAP or declare the field "
            f"explicitly on the factory."
        )
        raise NotImplementedError(msg)

    @classmethod
    def constraints_for_field(cls, field: models.Field) -> Constraints | None:
        constraints: Constraints = {}

        if getattr(field, "max_length", None):
            constraints["max_length"] = field.max_length
        if isinstance(field, models.CharField | models.TextField) and not field.blank:
            # PolyFactory will happily generate "" for a string constrained only by
            # max_length. Django's `blank=False` means empty is invalid, so give the
            # generator a floor rather than letting required columns come out empty.
            constraints["min_length"] = 1
        if isinstance(field, models.DecimalField):
            constraints["max_digits"] = field.max_digits
            constraints["decimal_places"] = field.decimal_places
        if isinstance(
            field,
            models.PositiveIntegerField
            | models.PositiveSmallIntegerField
            | models.PositiveBigIntegerField,
        ):
            constraints["ge"] = 0

        return constraints or None

    @classmethod
    def _is_declared(cls, name: str) -> bool:
        """Whether the factory declares this field, using PolyFactory's own predicate."""
        return hasattr(cls, name) and not hasattr(BaseFactory, name)

    @classmethod
    def should_set_field_value(cls, field_meta: FieldMeta, **kwargs: Any) -> bool:
        """Skip undeclared ForeignKeys unless __set_foreign_keys__ is on.

        The base implementation already returns False when the caller passed the field
        as a kwarg, which is what gives us FactoryBot's association-override semantics
        for free.
        """
        if not super().should_set_field_value(field_meta, **kwargs):
            return False

        if field_meta.name in cls._relation_field_names() and not cls.__set_foreign_keys__:
            return cls._is_declared(field_meta.name)

        return True

    @classmethod
    def _relation_field_names(cls) -> frozenset[str]:
        return frozenset(
            field.name
            for field in cls.__model__._meta.get_fields()
            if isinstance(field, models.Field) and field.is_relation
        )

    # ---- the one piece of real surgery ----
    @classmethod
    def get_field_value(
        cls,
        field_meta: FieldMeta,
        field_build_parameters: Any | None = None,
        build_context: Any | None = None,
    ) -> Any:
        """Persist related models instead of merely building them.

        `BaseFactory.get_field_value` resolves a sub-model annotation with `.build()`,
        which leaves the related row unsaved. Django then refuses the parent save with
        "save() prohibited to prevent data loss due to unsaved related object". Only
        reachable when `__set_foreign_keys__` is True.
        """
        for candidate in get_args(field_meta.annotation) or (field_meta.annotation,):
            if isinstance(candidate, type) and issubclass(candidate, models.Model):
                return cls._get_or_create_factory(model=candidate).create_sync()

        return super().get_field_value(field_meta, field_build_parameters, build_context)
