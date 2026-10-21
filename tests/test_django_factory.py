"""The PolyFactory Django adapter, tested in its own right.

Proven before anything depends on it: if the adapter is subtly wrong, every test that
uses it fails for the wrong reason.
"""

import datetime as dt

import pytest

from tests.factories.base import DjangoModelFactory
from tests.factories.models import AuthorFactory, WidgetFactory
from tests.testapp.models import Author, Widget

pytestmark = pytest.mark.django_db


class BareAuthorFactory(DjangoModelFactory[Author]):
    """No declared fields: exercises the adapter's type mapping and constraints."""

    __model__ = Author


class BareWidgetFactory(DjangoModelFactory[Widget]):
    __model__ = Widget


class AutoFkWidgetFactory(DjangoModelFactory[Widget]):
    """Opts in to implicit ForeignKey resolution."""

    __model__ = Widget
    __set_foreign_keys__ = True


def test_build_generates_type_correct_values() -> None:
    widget = WidgetFactory.build()

    assert isinstance(widget.name, str)
    assert isinstance(widget.price_cents, int)
    assert isinstance(widget.quantity, int)


def test_build_respects_max_length_constraints() -> None:
    """Django max_length is carried into PolyFactory Constraints.

    Uses a bare factory with no declared fields, so the value really comes from the
    adapter's type mapping and constraints rather than from a Use(...) callable.
    """
    max_length = Author._meta.get_field("name").max_length
    lengths = [len(BareAuthorFactory.build().name) for _ in range(50)]

    assert lengths
    assert max(lengths) <= max_length
    assert min(lengths) > 0


def test_foreign_keys_are_skipped_unless_opted_in() -> None:
    """Undeclared FKs stay unset, so a model with mutually-exclusive FKs stays valid."""
    assert "author" not in BareWidgetFactory.build().__dict__ or (
        BareWidgetFactory.build().author_id is None
    )


def test_set_foreign_keys_opt_in_persists_the_related_row() -> None:
    """The escape hatch dispatches to create_sync(), not build().

    PolyFactory's own sub-model resolution uses .build(), which would leave the parent
    unsaved and make Django refuse the child save.
    """
    widget = AutoFkWidgetFactory.create_sync()

    assert widget.author_id is not None
    assert Author.objects.filter(pk=widget.author_id).exists()


def test_build_leaves_primary_key_and_auto_timestamps_unset() -> None:
    """Which is what makes create_sync() a real INSERT, and lets the ORM stamp times."""
    author = AuthorFactory.build()

    assert author.pk is None
    assert author.created_at is None
    assert author.updated_at is None


def test_create_sync_persists_and_backfills() -> None:
    author = AuthorFactory.create_sync()

    assert author.pk is not None
    assert isinstance(author.created_at, dt.datetime)
    assert isinstance(author.updated_at, dt.datetime)
    assert Author.objects.count() == 1


def test_create_batch_sync_persists_every_instance() -> None:
    authors = AuthorFactory.create_batch_sync(3)

    assert len(authors) == 3
    assert Author.objects.count() == 3
    assert all(author.pk is not None for author in authors)


def test_declared_association_is_persisted() -> None:
    """Use(ParentFactory.create_sync) saves the parent, so the FK is usable."""
    widget = WidgetFactory.create_sync()

    assert widget.author_id is not None
    assert Author.objects.count() == 1
    assert Widget.objects.count() == 1


def test_passing_an_association_uses_it_and_creates_no_extra_parent() -> None:
    """FactoryBot's override semantics, which PolyFactory gives us for free.

    should_set_field_value() returns `field_meta.name not in kwargs`, so the declared
    Use(...) callable never runs when the caller supplies the value.
    """
    existing = AuthorFactory.create_sync()

    widget = WidgetFactory.create_sync(author=existing)

    assert widget.author_id == existing.pk
    assert Author.objects.count() == 1


def test_caller_kwargs_win_over_generated_values() -> None:
    widget = WidgetFactory.build(name="specific", price_cents=4000)

    assert widget.name == "specific"
    assert widget.price_cents == 4000


def test_nullable_fields_are_populated_deterministically() -> None:
    """Nullable columns get a concrete value unless the factory declares None.

    PolyFactory skips non-required fields at random, so the adapter marks every field
    required and leaves nulls to explicit declaration.
    """
    notes = {WidgetFactory.build().note for _ in range(10)}

    assert None not in notes


def test_unmapped_field_types_fail_loudly() -> None:
    """A plausible-looking wrong value is worse than an error."""
    from django.db import models

    from tests.factories.base import DjangoModelFactory

    class Unmapped(models.Field):
        pass

    with pytest.raises(NotImplementedError, match="no type mapping"):
        DjangoModelFactory.annotation_for_field(Unmapped(name="mystery"))
