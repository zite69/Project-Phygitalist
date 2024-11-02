from oscar.apps.catalogue.abstract_models import *
from oscar.core.loading import is_model_registered
from shop.apps.seller.models import Seller
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

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

for a, c in abstract_models.items():
    #exec(f"{c} = type('{c}', ({a.__name__}, ), {{ 'seller': models.ForeignKey(Seller, verbose_name=_('Seller'), on_delete=models.CASCADE, blank=False, null=False)}})")
    globals()[c] = type(c, (a, ),
                    {
                        'seller': models.ForeignKey(Seller, on_delete=models.CASCADE, blank=False, null=False, default=1),
                        '__module__': 'shop.apps.catalogue.models'
                    }
                    )

"""
This code produces the commented out code below it
"""
for mod in ["ProductCategory", "AttributeOptionGroup", "AttributeOption", "ProductRecommendation", "ProductImage", "ProductAttribute", "ProductAttributeValue" ]:
    exec(f"if not is_model_registered('catalogue', '{mod}'):\n    {mod} = type('{mod}', (eval('Abstract{mod}'),), {{ '__module__': 'shop.apps.catalogue.models'}})")

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
