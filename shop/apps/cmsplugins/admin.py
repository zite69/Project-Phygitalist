from django.contrib import admin
from shop.apps.cmsplugins.models import FeaturedProduct, FeaturedProductCollection


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    autocomplete_fields = ["product"]


@admin.register(FeaturedProductCollection)
class FeaturedProductCollectionAdmin(admin.ModelAdmin):
    pass
