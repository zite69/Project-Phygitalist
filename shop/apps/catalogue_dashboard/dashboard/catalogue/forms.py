from oscar.apps.dashboard.catalogue import forms as originalforms
from oscar.core.loading import get_model

ProductClass = get_model("catalogue", "ProductClass")

class ProductClassForm(originalforms.ProductClassForm):
    class Meta:
        model = ProductClass
        fields = ["seller", "name", "requires_shipping", "track_stock", "options"]
