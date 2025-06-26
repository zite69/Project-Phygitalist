from oscar.apps.catalogue.admin import *  
from django.contrib import admin
from shop.apps.catalogue.models import Product, Category, ProductAttribute, ProductClass
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
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

class ProductClassResource(resources.ModelResource):
    class Meta:
        model = ProductClass

admin.site.unregister(ProductAttribute)
admin.site.unregister(Product)
admin.site.unregister(Category)
admin.site.unregister(ProductClass)

@admin.register(Product)
class ProductImportExportModelAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]

@admin.register(Category)
class CategoryImportExportModelAdmin(ImportExportModelAdmin):
    resource_classes = [CategoryResource]

@admin.register(ProductAttribute)
class ProductAttributeImportExportModelAdmin(ImportExportModelAdmin):
    resource_classes = [ProductAttributeResource]

@admin.register(ProductClass)
class ProductClassImportExportModelAdmin(ImportExportModelAdmin):
    resource_classes = [ProductClassResource]
