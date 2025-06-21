from typing import List
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from oscar.apps.catalogue.views import (
    ProductDetailView as OGProductDetailView, CatalogueView as OGCatalogueView,
    ProductCategoryView as OGProductCategoryView
    )
from shop.apps.catalogue.models import Product, Category
from shop.apps.main.forms import BuyQuickForm

import logging

logger = logging.getLogger(__package__)

class ProductDetailView(OGProductDetailView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['buyquick_form'] = BuyQuickForm()

        return ctx

class CatalogueView(ListView):
    template_name = 'oscar/catalogue/browse.html'
    context_object_name = 'products'
    model = Product

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(stockrecords__num_in_stock__gt=0)
        return qs

class ProductCategoryView(ListView):
    paginate_by = 1
    template_name = 'oscar/catalogue/category.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = Category.objects.get(id=self.kwargs.get('pk'))
        return ctx

    def get_queryset(self):
        return Product.objects.filter(categories__in=[self.kwargs['pk']], stockrecords__num_in_stock__gt=0)

