from django import forms
from shop.apps.membership.models import Membership, Subscription, UserSubscription

class CreateMembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['name', 'description', 'type', 'public']
