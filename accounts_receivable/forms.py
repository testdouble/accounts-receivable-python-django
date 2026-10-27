"""Forms for the domain models."""

from django import forms

from accounts_receivable.models import Client

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
