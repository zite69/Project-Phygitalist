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
from shop.apps.main.models import BaseLogModelMixin
from shop.apps.user.models import validate_length
from shop.apps.main.storages import protected_storage

def gstin_upload_path(instance, filename):
    return f"sellers/{instance.user.id}/gstin/{filename}"

def pan_upload_path(instance, filename):
    return f"seller/{instance.user.id}/pan/{filename}"

class AbstractSeller(BaseLogModelMixin):
    name = models.CharField(_("Shop Name"), max_length=128, unique=True, blank=False, null=False, db_index=True)
    handle = models.SlugField(_("Shop Handle"), max_length=20, unique=True, blank=False, null=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=False, null=False,
        verbose_name=_("Seller User"), on_delete=models.PROTECT, related_name="seller")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
        verbose_name=_("Shop Admin"), on_delete=models.PROTECT, related_name="seller_admins")
    ceo = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name="seller_ceos")
    gstin = models.CharField(_("GSTIN Number"), name="gstin", max_length=15, blank=True,
        db_index=True, null=True, validators=[validate_length(15)])
    gstin_verified = models.BooleanField(_("GSTIN verified by Admin"), default=False, blank=True, null=True)

    gstin_file = models.FileField(verbose_name=_("Photo or scan of GSTIN"), upload_to=gstin_upload_path, storage=protected_storage, null=True)
    gstin_file_verified = models.BooleanField(_("Photo or scan of GSTIN has been verified by Admin"), default=False, blank=True, null=True)

    pan = models.CharField(_("PAN Number"), name="pan", max_length=10, db_index=True, blank=True,
        null=True, validators=[validate_length(10)])
    pan_verified = models.BooleanField(_("PAN Number verified by Admin"), default=False, blank=True, null=True)

    pan_file = models.FileField(_("Photo or scan of PAN card"), upload_to=pan_upload_path, storage=protected_storage, null=True)
    pan_file_verified = models.BooleanField(_("Photo or scan of PAN card verified by Admin"), default=False, blank=True, null=True)

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


