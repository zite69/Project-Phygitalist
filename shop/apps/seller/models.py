from django.db import models
from oscar.core.loading import is_model_registered
from .abstract_models import AbstractSeller, AbstractSellerAddress, AbstractSellerPickupAddress
import logging

logger = logging.getLogger(__name__)

if not is_model_registered("seller", "Seller"):
    class Seller(AbstractSeller):
        pass

if not is_model_registered("seller", "SellerAddress"):
    class SellerAddress(AbstractSellerAddress):
        pass

if not is_model_registered("seller", "SellerPickupAddress"):
    class SellerPickupAddress(AbstractSellerPickupAddress):
        pass

