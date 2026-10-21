"""Throwaway models used only to exercise the PolyFactory Django adapter.

These are NOT domain models. They exist so `tests/test_django_factory.py` can prove
the adapter against the field shapes the real domain will use -- a parent, a child
with a ForeignKey, integer cents, a nullable string, a default, and auto timestamps --
without inventing application models or a migration we would later throw away.

This app ships no migrations package, so Django's test-database setup creates these
tables via `migrate --run-syncdb`.
"""

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class Widget(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="widgets")
    name = models.CharField(max_length=60)
    price_cents = models.IntegerField()
    quantity = models.IntegerField(default=1)
    note = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name
