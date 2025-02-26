from django import forms
from django.conf import settings

class RazorpayForm(forms.Form):
    key = forms.CharField(widget=forms.HiddenInput(), initial=settings.RAZORPAY_KEY, max_length=64)
    amount = forms.IntegerField()
    name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    order_id = forms.CharField(max_length=12)
