from django.db import models
from oscar.core.loading import is_model_registered
from .abstract_models import AbstractSeller
import logging

logger = logging.getLogger("shop.apps.seller")

if not is_model_registered("seller", "Seller"):
    class Seller(AbstractSeller):
        pass
