from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import admin
from phonenumber_field.modelfields import PhoneNumberField
from shop.apps.user.models import validate_length, Profile, User
from typing import Any, Self
from shop.apps.main.models import Postoffice
import os
import logging

logger = logging.getLogger("shop.apps.registration")

@deconstructible
class unique_in_db(object):
    def __init__(self, model, field) -> None:
        self.model = model
        self.field = field

    def __call__(self, value, **kwds: Any) -> Any:
        q = Q(**{f"{self.field}": value})
        ps = self.model.objects.filter(q)
        if ps:
            raise ValidationError(_("%(field)s with value %(value)s already exists in our %(model)s databases! Please check the number or login with your registered ID"),
                                  params={"value": value, "field": self.field, "model": self.model}
                  )

    def __eq__(self, other: Self) -> bool:
        return self.field == other.field and self.model == other.model

class SellerRegistration(models.Model):
    STATUS_APPROVED = 'A'
    STATUS_PENDING = 'P'
    STATUS_REJECTION_TEMPORARY = 'T'
    STATUS_REJECTED = 'R'
    STATUS_IN_PROGRESS = 'I'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTION_TEMPORARY, 'Temporarily Rejected'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_IN_PROGRESS, 'Inprogress')
    )
    
    GST_STATUS_HAVE = 'Y'
    GST_STATUS_DONT = 'N'
    GST_STATUS_EXEMPT = 'E'
    GST_STATUS_LATER = 'L'

    GST_STATUS_CHOICES = [
        (GST_STATUS_HAVE, 'I have GST'),
        (GST_STATUS_DONT, "I don't have GST"),
        (GST_STATUS_EXEMPT, 'I am expemted'),
        (GST_STATUS_LATER, 'I will add later')
    ]

    name = models.CharField(_("Full Name"), blank=False, null=False, max_length=64)
    shop_name = models.CharField(_("Shop Name"), blank=False, null=False, max_length=128)
    shop_handle = models.SlugField(_("Shop Handle"), blank=False, null=False, max_length=20)
    phone = PhoneNumberField(_("Phone Number"), db_index=True, blank=True, null=True)
    email = models.EmailField(_("Email Adderss"), db_index=True, blank=True, null=True)

    gst_status = models.CharField(_("GST Status"), max_length=2, choices=GST_STATUS_CHOICES, db_index=True, blank=False, null=False, default=GST_STATUS_HAVE)
    gstin = models.CharField(_("GSTIN Number"), name="gstin", max_length=15, blank=True,
        db_index=True, null=True,
        validators=[validate_length(15)])
    gstin_verified = models.BooleanField(_("GSTIN Verified by Admin"), default=False, blank=True, null=True)

    pan = models.CharField(_("PAN Number"), name="pan", max_length=10, db_index=True, blank=True,
        null=True, validators=[validate_length(10)])
    pan_verified = models.BooleanField(_("PAN Number verified by Admin"), default=False, blank=True, null=True)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='seller_registration')
    postoffice = models.ForeignKey(Postoffice, on_delete=models.PROTECT, null=True)

    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='approved_sellers')
    approved_on = models.DateTimeField(_("Approved On"), null=True)
    approval_notes = models.TextField(_("Approval/Rejection Reasons"), blank=True, null=True)
    approval_status = models.CharField(_("Approval Status"), choices=STATUS_CHOICES, max_length=2, db_index=True, default=STATUS_IN_PROGRESS)

    @property
    def approved(self):
        return self.approval_status == SellerRegistration.STATUS_APPROVED

    def get_pincode(self):
        return self.postoffice.pincode


    def gst_status_label(self):
        for k, v in SellerRegistration.GST_STATUS_CHOICES:
            if self.gst_status == k:
                return v

        return ""

    def get_approval_status(self):
        for k, v in SellerRegistration.STATUS_CHOICES:
            if self.approval_status == k:
                return v

        return ""

    def clean(self):
        logger.debug("Inside model clean")
        if self.gstin and self.gstin != "":
            # Check for unique GST across SellerRegistration and Profile
            others = SellerRegistration.objects.filter(gstin=self.gstin).exclude(pk=self.pk)
            if others.count() > 0:
                raise ValidationError(_("This GSTIN number already exists in our database. Please check the number or login with your registered ID"))
            
            others = Profile.objects.filter(gstin=self.gstin).exclude(user__seller_registration=self)
            if others.count() > 0:
                raise ValidationError(_("This GSTIN number already exists in our database. Please check the number or login with your registered ID"))

        if self.pan and self.pan != "":
            # Check for unique PAN across SellerRegistration and Profile
            others = SellerRegistration.objects.filter(pan=self.pan).exclude(pk=self.pk)
            if others.count() > 0:
                raise ValidationError(_("This PAN number already exists in our database. Please check the number of login with your registered ID"))

            others = Profile.objects.filter(pan=self.pan).exclude(user__seller_registration=self)
            if others.count() > 0:
                raise ValidationError(_("This PAN number already exists in our database. Please check the number or login with your registered ID"))

        if self.phone:
            # Check phone number
            others = SellerRegistration.objects.filter(phone=self.phone).exclude(pk=self.pk)
            if others.count() > 0:
                raise ValidationError(_("This phone number already exists in our database. Please check the number or login with your registered ID"))

            others = User.objects.filter(phone=self.phone).exclude(seller_registration=self)
            if others.count() > 0:
                raise ValidationError(_("This phone number already exists in our database. Please check the number or login with your registered ID"))

        if self.email and self.email != "":
            # Check email address
            others = SellerRegistration.objects.filter(email=self.email).exclude(pk=self.pk)
            if others.count() > 0:
                logger.debug(f"Found email in SellerRegistration email:{self.email} pk: {self.pk}")
                raise ValidationError(_("This email already exists in our database. Please check the number or login with your registered ID"))

            others = User.objects.filter(email=self.email).exclude(seller_registration=self)
            if others.count() > 0:
                logger.debug(f"Found email in User email: {self.email} self: {self}")
                raise ValidationError(_("This email already exists in our database. Please check the number or login with your registered ID"))


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['gstin'],
                condition=(~models.Q(gstin='') & models.Q(gstin__isnull=False)),
                name='unique_gstin_ifnotnull'
                ),
            models.UniqueConstraint(
                fields=['pan'],
                condition=(~models.Q(pan='') & models.Q(pan__isnull=False)),
                name='unique_pan_insellerreg_ifnotnull'
            )
        ]

    def __str__(self):
        if self.shop_handle != '':
            return self.shop_handle
        elif self.phone != None:
            return str(self.phone)

seller_registration_filestorage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))

class SellerProduct(models.Model):
    seller_reg = models.ForeignKey(SellerRegistration, on_delete=models.PROTECT)
    name = models.CharField(_("Product Service Name"), max_length=255, blank=False, null=False)
    image = models.ImageField(_("Product Image"), upload_to="uploads/sellerreg/%Y/%m/%d", storage=seller_registration_filestorage)
