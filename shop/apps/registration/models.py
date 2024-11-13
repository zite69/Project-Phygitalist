from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from phonenumber_field.modelfields import PhoneNumberField
from shop.apps.user.models import validate_length, Profile, User
from typing import Any, Self
from shop.apps.main.models import Pincode
import os

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
        return self.field == other.field

class SellerRegistration(models.Model):
    STATUS_APPROVED = 'A'
    STATUS_PENDING = 'P'
    STATUS_REJECTION_TEMPORARY = 'T'
    STATUS_REJECTED = 'R'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTION_TEMPORARY, 'Temporarily Rejected'),
        (STATUS_REJECTED, 'Rejected')
    )

    name = models.CharField(_("Full Name"), blank=False, null=False, max_length=64)
    shop_name = models.CharField(_("Shop Name"), blank=False, null=False, max_length=128)
    shop_handle = models.SlugField(_("Shop Handle"), blank=False, null=False, max_length=20)
    phone = PhoneNumberField(_("Phone Number"), db_index=True, blank=False, validators=[unique_in_db(User, 'phone')])
    email = models.EmailField(_("Email Adderss"), db_index=True, blank=False, validators=[unique_in_db(User, 'email')])
    gstin = models.CharField(_("GSTIN Number"), name="gstin", max_length=15, blank=False,
        db_index=True, null=True,
        validators=[validate_length(15), unique_in_db(Profile, 'gstin')])
    pan = models.CharField(_("PAN Number"), name="pan", max_length=10, db_index=True, blank=False,
        null=True, validators=[validate_length(10), unique_in_db(Profile, 'pan')])

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='seller_registration')
    pincode = models.ForeignKey(Pincode, on_delete=models.PROTECT, null=True)

    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='approved_sellers')
    approved_on = models.DateTimeField(_("Approved On"), null=True)
    approval_notes = models.TextField(_("Approval/Rejection Reasons"), blank=True, null=True)
    approval_status = models.CharField(_("Approval Status"), max_length=2, db_index=True, default=STATUS_PENDING)

    @property
    def approved(self):
        return self.approval_status == self.__class__.STATUS_APPROVED

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

seller_registration_filestorage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads', 'sellerreg'))

class SellerProduct(models.Model):
    seller_reg = models.ForeignKey(SellerRegistration, on_delete=models.PROTECT)
    name = models.CharField(_("Product Service Name"), max_length=255, blank=False, null=False)
    image = models.ImageField(_("Product Image"), upload_to="uploads/sellerreg/%Y/%m/%d", storage=seller_registration_filestorage)
