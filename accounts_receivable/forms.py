"""Forms for the domain models."""

from django import forms

from accounts_receivable.models import Client, Product, Service

FIELD_CLASSES = (
    "block w-full rounded-md border border-[#e4e4e4] bg-white px-3 py-2 text-sm "
    "placeholder:text-gray-400 focus:border-brand focus:outline-none focus:ring-1 "
    "focus:ring-brand"
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
