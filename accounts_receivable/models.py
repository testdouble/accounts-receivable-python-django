"""Domain models ported from the Rails source app.

The remaining two tables (invoices, line_items) land in a later pass; this one covers
`clients`, `products` and `services`.
"""

from django.db import models
from django.urls import reverse


class Client(models.Model):
    """A customer who receives invoices.

    The Rails source declares `name` and `email` as `string, null: false` with no length
    cap -- SQLite ignores varchar limits. Django requires `max_length`, so the caps below
    are a port artifact rather than a domain rule.
    """

    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land, matching the Rails scaffold's redirect."""
        return reverse("client_detail", kwargs={"pk": self.pk})


class Product(models.Model):
    """Something sold by the unit, which a line item can reference.

    `max_length` is the same port artifact as on `Client`. `price_cents` is the Rails
    source's `t.integer` -- signed, and with an empty model body behind it, so a negative
    price is accepted here exactly as it is there.

    Products and services are two independent tables in the Rails schema with identical
    columns. They stay duplicated rather than sharing an abstract base, because an
    abstract parent is a shape the source does not have.
    """

    name = models.CharField(max_length=120)
    price_cents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land, matching the Rails scaffold's redirect."""
        return reverse("product_detail", kwargs={"pk": self.pk})


class Service(models.Model):
    """Work that is billed for, which a line item can reference.

    Same columns as `Product`; see the note there on the duplication and on
    `price_cents` accepting a negative value.
    """

    name = models.CharField(max_length=120)
    price_cents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land, matching the Rails scaffold's redirect."""
        return reverse("service_detail", kwargs={"pk": self.pk})
