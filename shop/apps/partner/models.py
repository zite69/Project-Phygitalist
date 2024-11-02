from oscar.apps.partner.abstract_models import *
from oscar.apps.address.abstract_models import AbstractPartnerAddress
""" from oscar.apps.partner.models import (
    PartnerAddress,
    StockRecord,
    StockAlert
) """
from shop.apps.seller.models import Seller
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from oscar.core.loading import is_model_registered


class Partner(AbstractPartner):
    seller = models.ForeignKey(Seller, verbose_name=_("Seller"), blank=False, null=False, default=settings.ZITE69_MAIN_SELLER_ID, on_delete=models.CASCADE)

if not is_model_registered('partner', 'PartnerAddress'):
    class PartnerAddress(AbstractPartnerAddress):
        pass

if not is_model_registered('partner', 'StockRecord'):
    class StockRecord(AbstractStockRecord):
        pass

if not is_model_registered('partner', 'StockAlert'):
    class StockAlert(AbstractStockAlert):
        pass


