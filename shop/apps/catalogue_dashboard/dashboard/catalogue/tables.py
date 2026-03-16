from os import access
from django.db.models.expressions import Col
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_model
from oscar.apps.dashboard.catalogue import tables as originaltables
from django_tables2 import Column, A
from oscar.apps.dashboard.catalogue.tables import CategoryTable

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")

class CategoryTableReadOnly(CategoryTable):
    name = Column()
    num_children = Column(
        verbose_name=_("Number of child categories"),
        accessor="get_num_children",
        orderable=False,
    )

    class Meta(CategoryTable.Meta):
        sequence = ("name", "description", "...", "is_public")
        exclude = ("actions",)


class ProductTable(originaltables.ProductTable):
    seller = Column(
                verbose_name=_("Seller"),
                accessor= A("seller")
            )

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("upc", "qc_status", "is_public", "date_updated")
        sequence = (
            "seller",
            "title",
            "upc",
            "image",
            "product_class",
            "variants",
            "stock_records",
            "qc_status",
            "...",
            "is_public",
            "date_updated",
            "actions",
        )
 
