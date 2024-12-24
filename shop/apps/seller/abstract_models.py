from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.core.cache import cache
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
    ObjectDoesNotExist,
)
from django.core.files.base import File
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum

from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from djangocms_form_builder import verbose_name
from oscar.core.loading import get_class, get_model
from shop.apps.main.models import BaseLogModelMixin
from shop.apps.user.models import validate_length
from shop.apps.address.abstract_models import AbstractAddress
from shop.apps.main.storages import protected_storage, ProtectedStorage

def gstin_upload_path(instance, filename):
    return f"seller/{instance.user.id}/gstin/{filename}"

def pan_upload_path(instance, filename):
    return f"seller/{instance.user.id}/pan/{filename}"

def signature_upload_path(instance, filename):
    return f"seller/{instance.user.id}/signature/{filename}"

class AbstractSeller(BaseLogModelMixin):
    SHIPPING_SELF, SHIPPING_ZITE69 = ('S', 'Z')
    SHIPPING_CHOICES = (
            (SHIPPING_SELF, _("Self Shipping")),
            (SHIPPING_ZITE69, _("zite69 Shipping (coming soon)"))
    )

    name = models.CharField(_("Shop Name"), max_length=128, unique=True, blank=False, null=False, db_index=True)
    handle = models.SlugField(_("Shop Handle"), max_length=20, unique=True, blank=False, null=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False,
        verbose_name=_("Seller User"), on_delete=models.PROTECT, related_name="seller")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
        verbose_name=_("Shop Admin"), on_delete=models.PROTECT, related_name="seller_admins")
    ceo = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="seller_ceos")

    gstin = models.CharField(_("GSTIN Number"), name="gstin", max_length=15, blank=True,
        db_index=True, null=True, validators=[validate_length(15)])
    gstin_verified = models.BooleanField(_("GSTIN verified by Admin"), default=False)

    gstin_file = models.ImageField(verbose_name=_("Photo or scan of GSTIN"), upload_to=gstin_upload_path, storage=ProtectedStorage(), null=True)
    gstin_file_verified = models.BooleanField(_("Photo or scan of GSTIN has been verified by Admin"), default=False)

    pan = models.CharField(_("PAN Number"), name="pan", max_length=10, db_index=True, blank=False,
        null=True, validators=[validate_length(10)])
    pan_verified = models.BooleanField(_("PAN Number verified by Admin"), default=False)

    pan_file = models.ImageField(_("Photo or scan of PAN card"), upload_to=pan_upload_path, storage=ProtectedStorage(), null=True)
    pan_file_verified = models.BooleanField(_("Photo or scan of PAN card verified by Admin"), default=False)

    signature_file = models.ImageField(_("Photo or scan of signature"), upload_to=signature_upload_path, storage=ProtectedStorage(), null=True)
    signature_file_verified = models.BooleanField(_("Photo or scan of signature verified by Admin"), default=False)
    shipping_preference = models.CharField(_("Shipping Preference"), blank=True, max_length=1, choices=SHIPPING_CHOICES, default=SHIPPING_SELF)

    approved = models.BooleanField(_("Seller Approved by Admin"), default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="approved_sellers")
    approved_on = models.DateTimeField(_("When the Seller was approved"), null=True)

    class Meta:
        abstract = True
        app_label = "seller"
        ordering = ["name"]
        verbose_name = _("Seller")
        verbose_name_plural = _("Sellers")
        constraints = [
            models.UniqueConstraint(
                fields=['gstin'],
                condition=(~models.Q(gstin='') & models.Q(gstin__isnull=False)),
                name='unique_gstin_in_seller_ifnotnull'
                ),
            models.UniqueConstraint(
                fields=['pan'],
                condition=(~models.Q(pan='') & models.Q(pan__isnull=False)),
                name='unique_pan_in_seller_ifnotnull'
            )
        ]

class AbstractSellerAddress(AbstractAddress):
    seller = models.ForeignKey(
            "seller.Seller",
            on_delete=models.CASCADE,
            related_name="addresses",
            verbose_name=_("Seller")
            )

    class Meta:
        abstract = True
        app_label = "seller"
        verbose_name = _("Seller address")
        verbose_name_plural = _("Seller addresses")

class AbstractSellerPickupAddress(AbstractAddress):
    seller = models.ForeignKey(
            "seller.Seller",
            on_delete=models.CASCADE,
            related_name="pickup_addresses",
            verbose_name=_("Seller")
            )

    class Meta:
        abstract = True
        app_label = "seller"
        verbose_name = _("Seller Pickup Address")
        verbose_name_plural = _("Seller Pickup Addresses")

