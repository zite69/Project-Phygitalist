from django import forms
from django.utils.translation import pgettext_lazy, gettext_lazy as _
from oscar.apps.dashboard.partners import forms as originalforms
from oscar.core.loading import get_model

Seller = get_model("seller", "Seller")
Partner = get_model('partner', 'Partner')

class PartnerSearchForm(originalforms.PartnerSearchForm):
    seller = forms.ModelChoiceField(
            label=_("Seller"),
            empty_label=_("--Choose Seller--"),
            queryset=Seller.objects.all(),
            required=False
            )

    name = forms.CharField(
        required=False, label=pgettext_lazy("Partner's name", "Name")
    )

    field_order = ['seller', 'name']

class PartnerCreateForm(originalforms.PartnerCreateForm):
    class Meta:
        model = Partner
        fields = ['sellers', 'name']
