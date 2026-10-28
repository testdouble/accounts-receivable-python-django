"""Domain models ported from the Rails source app.

All five tables from the Rails `db/schema.rb`: `clients`, `products`, `services`,
`invoices` and `line_items`.
"""

import datetime as dt

from django.core.exceptions import ValidationError
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


class Invoice(models.Model):
    """A bill addressed to one client, totalled from its line items.

    The Rails source's columns verbatim: a client, a `net_days` payment window, and a
    free-text `note`. There is no subject or issue-date column -- the show page prints
    the note as the invoice's subject line, and `created_at` is the issue date that the
    due date is measured from.
    """

    # Rails declares `add_foreign_key "invoices", "clients"` with no cascade, so deleting
    # a client that has invoices raises there. PROTECT is the same contract.
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="invoices")
    net_days = models.IntegerField(default=30)
    # Rails' `t.string "note"` is nullable. `blank=True` storing "" is Django's spelling
    # for the same optional column; `null=True` on a text field means two kinds of empty.
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        """Matches the heading on the Rails show page, which has no better name to use."""
        return f"Invoice #{self.pk}"

    def get_absolute_url(self) -> str:
        """Where create and update land, matching the Rails scaffold's redirect."""
        return reverse("invoice_detail", kwargs={"pk": self.pk})

    @property
    def due_date(self) -> dt.date | None:
        """`created_at.to_date + net_days`, exactly as the Rails show page computes it.

        Derived from the stored `created_at` rather than from the clock, so it does not
        move between requests -- and so there is no naive `date.today()` to get wrong.
        None before the row is saved, since `auto_now_add` has not run yet.
        """
        if self.created_at is None:
            return None

        return self.created_at.date() + dt.timedelta(days=self.net_days)

    @property
    def total_cents(self) -> int:
        """Every line item's subtotal, summed.

        NOTE: the invoice **page** can print less than this. `InvoiceDetailView`
        preserves the Rails defect that drops line items priced from a zero-cost product
        or service, and computes its own total from what survives that filter. This
        property is the honest figure, and is what the JSON API serves. The two are meant
        to disagree; see CLAUDE.md, "Planted bugs are preserved".
        """
        return sum(item.subtotal_cents or 0 for item in self.line_items.all())


class LineItem(models.Model):
    """One billable row on an invoice, priced from a product or a service.

    Exactly one of `product` and `service` is set; see `clean()`. Both columns are
    nullable in the Rails schema with the rule enforced in the model, and that shape is
    what `tests/factories/base.py` keeps `__set_foreign_keys__` off for.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    # PROTECT, as on `Invoice.client`: the Rails foreign keys do not cascade.
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True, related_name="line_items"
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, null=True, blank=True, related_name="line_items"
    )
    # NULL means "no override, use the catalog price". It is not the same as an override
    # of 0, which is a deliberately free line -- see `unit_price_cents`.
    price_override_cents = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.description or f"Line item #{self.pk}"

    def get_absolute_url(self) -> str:
        return reverse("line_item_detail", kwargs={"pk": self.pk})

    def clean(self) -> None:
        if self.product_id is None and self.service_id is None:
            raise ValidationError("A line item must be either a product or a service")

        if self.product_id is not None and self.service_id is not None:
            raise ValidationError("A line item can't be both a product and a service")

    @property
    def unit_price_cents(self) -> int | None:
        if self.price_override_cents is not None:
            return self.price_override_cents

        catalog = self.product or self.service

        return catalog.price_cents if catalog else None

    @property
    def subtotal_cents(self) -> int | None:
        unit_price = self.unit_price_cents

        return None if unit_price is None else unit_price * self.quantity
