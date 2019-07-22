from django import forms
from .models import Order


class PaymentForm(forms.Form):
    name = forms.CharField(max_length=30)
    surname = forms.CharField(max_length=30)
    currency = forms.ChoiceField(choices=Order.CURRENCY)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
