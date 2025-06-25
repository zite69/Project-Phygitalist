from oscar.apps.catalogue.admin import *  
from django.contrib import admin
from shop.apps.catalogue.models import Product, Category, ProductAttribute
from import_export.admin import ImportExportModelAdmin
from import_export import resources

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product

class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category

class ProductAttributeResource(resources.ModelResource):
    class Meta:
        model = ProductAttribute

admin.site.unregister(ProductAttribute)
admin.site.unregister(Product)
admin.site.unregister(Category)

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_classes = [CategoryResource]

@admin.register(ProductAttribute)
class ProductAttributeAdmin(ImportExportModelAdmin):
    resource_classes = [ProductAttributeResource]

