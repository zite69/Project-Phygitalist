from django import forms
from django.db.models import query
from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.catalogue import forms as originalforms
from oscar.core.loading import get_model
from shop.apps.seller.models import Seller

Product = get_model("catalogue", "Product")

class ProductForm(originalforms.ProductForm):
    class Meta:
        model = Product
        fields = [
            "seller",
            "title",
            "upc",
            "description",
            "is_public",
            "is_discountable",
            "structure",
            "slug",
            "meta_title",
            "meta_description",
        ]

