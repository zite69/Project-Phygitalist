from typing import List
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from oscar.apps.catalogue.views import (
    ProductDetailView as OGProductDetailView, CatalogueView as OGCatalogueView,
    ProductCategoryView as OGProductCategoryView
    )
from shop.apps.catalogue.models import Product
import logging
logger = logging.getLogger(__package__)

class ProductDetailView(OGProductDetailView):
    pass

class CatalogueView(ListView):
    template_name = 'oscar/catalogue/browse.html'
    context_object_name = 'products'
    model = Product

class ProductCategoryView(ListView):
    paginate_by = 1
    template_name = 'oscar/catalogue/category.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(categories__in=[self.kwargs['pk']])

