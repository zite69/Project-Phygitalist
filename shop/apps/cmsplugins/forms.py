from django import forms
from django_select2 import forms as s2forms
from . import models
from shop.apps.catalogue.models import Product
from django.utils.translation import gettext as _
import select2.fields

class ProductWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "title__icontains",
        "upc__icontains",
    ]

class FeaturedProductForm(forms.ModelForm):
    product = select2.fields.ChoiceField(
            choices=Product.objects_choices.all(),
            overlay="Select a Product"
            )
    # product = s2forms.ModelSelect2Field(
    #         queryset=Product.objects.all(),
    #         widget=s2forms.Select2Widget(attrs={"data-placeholder": "Select a Product"}),
    #         label=_("Product")
    #         )

    class Meta:
        model = models.FeaturedProduct
        fields = '__all__'
