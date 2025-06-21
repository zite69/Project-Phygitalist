from django.http.request import is_same_domain
from django.urls import reverse
from oscar.apps.catalogue.abstract_models import AbstractProduct, AbstractProductClass, AbstractProductAttribute, AbstractCategory, AbstractOption, AbstractProductCategory, AbstractAttributeOptionGroup, AbstractAttributeOption, AbstractProductRecommendation, AbstractProductImage, AbstractProductAttribute, AbstractProductAttributeValue
from oscar.core.loading import is_model_registered
from shop.apps.seller.models import Seller
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from shop.apps.main.utils.urls import get_absolute_url

"""
The following code is just meta code to create classes inside this file like
class Product(AbstractProduct):
    seller = models.ForeignKey(Seller, verbose_name=_("Seller"), blank=False, null=False, on_delete=models.CASCADE)

It will create a class called each of the elements in names from its corresponding Abstract{name} class
"""
names = ['Product', 'ProductClass', 'ProductAttribute', 'Category', 'Option']

abstract_models = { k:v for (k, v) in zip(list(map(lambda name: eval(f"Abstract{name}"), names)), names) }
"""
abstract_models = {
    AbstractProduct: 'Product',
    AbstractProductClass: 'ProductClass',
    AbstractProductAttribute: 'ProductAttribute',
    AbstractCategory: 'Category',
    AbstractOption: 'Option'
}
"""

#for a, c in abstract_models.items():
#    #exec(f"{c} = type('{c}', ({a.__name__}, ), {{ 'seller': models.ForeignKey(Seller, verbose_name=_('Seller'), on_delete=models.CASCADE, blank=False, null=False)}})")
#    globals()[c] = type(c, (a, ),
#                    {
#                        'seller': models.ForeignKey(Seller, on_delete=models.CASCADE, blank=False, null=False, default=1),
#                        '__module__': 'shop.apps.catalogue.models'
#                    }
#                    )

"""
This code produces the commented out code below it
"""
# for mod in ["ProductCategory", "AttributeOptionGroup", "AttributeOption", "ProductRecommendation", "ProductImage", "ProductAttribute", "ProductAttributeValue" ]:
#     exec(f"if not is_model_registered('catalogue', '{mod}'):\n    {mod} = type('{mod}', (eval('Abstract{mod}'),), {{ '__module__': 'shop.apps.catalogue.models'}})")

"""
if not is_model_registered("catalogue", "ProductCategory"):
    class ProductCategory(AbstractProductCategory):
        pass

if not is_model_registered("catalogue", "AttributeOptionGroup"):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass

if not is_model_registered("catalogue", "AttributeOption"):
    class AttributeOption(AbstractAttributeOption):
        pass

 """

if not is_model_registered("catalogue", "Product"):
    class Product(AbstractProduct):
        class QcStatus(models.TextChoices):
            NOT_SUBMITTED = 'NOT', _("Not Submitted")
            SUBMITTED = 'SUB', _("Submitted")
            APPROVED = 'APP', _("Approved")

        seller = models.ForeignKey(Seller, verbose_name=_("Seller"), on_delete=models.CASCADE,
                related_name="products", blank=False, null=False, default=settings.ZITE69_MAIN_SELLER_ID)
        qc_status = models.CharField(max_length=3, choices=QcStatus.choices, default=QcStatus.NOT_SUBMITTED)

        mrp = models.DecimalField(_("MRP"), decimal_places=2, max_digits=12, blank=True, null=True)
        
        def get_full_domain_url(self):
            return get_absolute_url(site_id=settings.DEFAULT_SITE_ID, view_name="catalogue:detail", 
                        product_slug=self.slug, pk=self.id)

        def get_absolute_url(self):
            if settings.SITE_ID == settings.DEFAULT_SITE_ID:
                return reverse(
                    "catalogue:detail", kwargs={"product_slug": self.slug, "pk": self.id}
                )
            else:
                return self.get_full_domain_url()    



        def get_qc_status(self):
            return self.QcStatus(self.qc_status).label

        def is_qc_submitted(self):
            return self.QcStatus(self.qc_status) == Product.QcStatus.SUBMITTED

        def is_qc_not_submitted(self):
            return self.QcStatus(self.qc_status) == Product.QcStatus.NOT_SUBMITTED

        def is_qc_approved(self):
            return self.QcStatus(self.qc_status) == Product.QcStatus.APPROVED

if not is_model_registered("catalogue", "ProductClass"):
    class ProductClass(AbstractProductClass):
        pass

if not is_model_registered("catalogue", "ProductAttribute"):
    class ProductAttribute(AbstractProductAttribute):
        pass

if not is_model_registered("catalogue", "Category"):
    class Category(AbstractCategory):
        pass

if not is_model_registered("catalogue", "Option"):
    class Option(AbstractOption):
        pass 

if not is_model_registered("catalogue", "ProductCategory"):
    class ProductCategory(AbstractProductCategory):
        pass

if not is_model_registered("catalogue", "AttributeOptionGroup"):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass

if not is_model_registered("catalogue", "AttributeOption"):
    class AttributeOption(AbstractAttributeOption):
        pass

if not is_model_registered("catalogue", "ProductRecommendation"):
    class ProductRecommendation(AbstractProductRecommendation):
        pass

if not is_model_registered("catalouge", "ProductImage"):
    class ProductImage(AbstractProductImage):
        pass

if not is_model_registered("catalouge", "ProductAttributeValue"):
    class ProductAttributeValue(AbstractProductAttributeValue):
        pass

