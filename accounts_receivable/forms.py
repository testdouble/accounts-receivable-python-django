"""Forms for the domain models."""

from django import forms

from accounts_receivable.models import Client, Invoice, LineItem, Product, Service

FIELD_CLASSES = (
    "block w-full rounded-md border border-[#e4e4e4] bg-white px-3 py-2 text-sm "
    "placeholder:text-gray-400 focus:border-brand focus:outline-none focus:ring-1 "
    "focus:ring-brand"
)

# Selects need the same frame but not the placeholder rule, and `pr-8` keeps the native
# arrow off the text.
SELECT_CLASSES = (
    "block w-full rounded-md border border-[#e4e4e4] bg-white py-2 pl-3 pr-8 text-sm "
    "focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email"]
        labels = {"email": "Billing email"}
        help_texts = {"email": "Shown as Attn on every invoice."}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Acme inc", "class": FIELD_CLASSES}),
            "email": forms.EmailInput(attrs={"placeholder": "ap@acme.com", "class": FIELD_CLASSES}),
        }


class ProductForm(forms.ModelForm):
    # No label override for `price_cents`: Django's default is "Price cents", which is
    # also what the Rails views print, verbatim.
    class Meta:
        model = Product
        fields = ["name", "price_cents"]
        help_texts = {"price_cents": "Whole cents. 20000 is $200.00."}
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Anti-virus software", "class": FIELD_CLASSES}
            ),
            "price_cents": forms.NumberInput(
                attrs={"placeholder": "20000", "class": FIELD_CLASSES}
            ),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "price_cents"]
        help_texts = {"price_cents": "Whole cents. 8000 is $80.00."}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Programming", "class": FIELD_CLASSES}),
            "price_cents": forms.NumberInput(attrs={"placeholder": "8000", "class": FIELD_CLASSES}),
        }


class InvoiceForm(forms.ModelForm):
    # Fields and their order are the Rails strong parameters verbatim:
    # `params.require(:invoice).permit(:client_id, :net_days, :note)`.
    class Meta:
        model = Invoice
        fields = ["client", "net_days", "note"]
        help_texts = {
            "net_days": "Days to pay. The due date is this many days after the invoice is created.",
            "note": "Printed as the invoice's subject line.",
        }
        widgets = {
            "client": forms.Select(attrs={"class": SELECT_CLASSES}),
            "net_days": forms.NumberInput(attrs={"placeholder": "30", "class": FIELD_CLASSES}),
            "note": forms.TextInput(
                attrs={
                    "placeholder": "Invoice for writing software for Acme",
                    "class": FIELD_CLASSES,
                }
            ),
        }


class LineItemForm(forms.ModelForm):
    # `params.require(:line_item).permit(:invoice_id, :product_id, :service_id,
    # :price_override_cents, :quantity, :description)`, in that order.
    #
    # Product and service both offer a blank option -- Rails' `include_blank: true` --
    # because exactly one of them is set. The model's `clean()` enforces that, and its
    # message arrives as a non-field error, which `line_items/form.html` renders.
    class Meta:
        model = LineItem
        fields = [
            "invoice",
            "product",
            "service",
            "price_override_cents",
            "quantity",
            "description",
        ]
        help_texts = {
            "product": "Set either a product or a service, not both.",
            "service": "Set either a product or a service, not both.",
            "price_override_cents": (
                "Whole cents. Leave blank to charge the product or service price; 0 is a free line."
            ),
            "quantity": "Units billed. Multiplied by the unit price for the subtotal.",
        }
        widgets = {
            "invoice": forms.Select(attrs={"class": SELECT_CLASSES}),
            "product": forms.Select(attrs={"class": SELECT_CLASSES}),
            "service": forms.Select(attrs={"class": SELECT_CLASSES}),
            "price_override_cents": forms.NumberInput(
                attrs={"placeholder": "4000", "class": FIELD_CLASSES}
            ),
            "quantity": forms.NumberInput(attrs={"placeholder": "40", "class": FIELD_CLASSES}),
            "description": forms.TextInput(
                attrs={"placeholder": "Amber's quality programming", "class": FIELD_CLASSES}
            ),
        }
