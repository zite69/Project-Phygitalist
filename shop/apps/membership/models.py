from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from filer.models import abstract
from djmoney.models.fields import MoneyField
from shop.apps.main.models import BaseLogModelMixin
from shop.apps.user.models import Profile
from datetime import datetime, timedelta

class Membership(BaseLogModelMixin):
    name = models.CharField(_("Membership Name"), blank=False, null=False, max_length=64, unique=True)
    description = models.TextField(_("Description of benefits of membership. Terms and Conditions"), blank=True, null=True)
    type = models.CharField(_("Membership Applies to Profile Type"), max_length=1, choices=Profile.TYPE_CHOICES, db_index=True)
    public = models.BooleanField(_("Is this Membership public"), default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT)

    #What permissions this Membership is allowed. At a model level
    permissions = models.ManyToManyField(Permission, related_name='permission_memberships', blank=True)

    #If this membership is not public, then which Users are allowed to take this membership
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='allowed_memberships', blank=True)
    #If this membership is not public, then which Groups are allowed to take this membership
    allowed_groups = models.ManyToManyField(Group, related_name='allowed_memberships', blank=True)

    class Meta:
        abstract = False
        app_label = _("membership")
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")


class Subscription(BaseLogModelMixin):
    name = models.CharField(_("Subscription Name"), blank=False, null=False, max_length=64, db_index=True)
    description = models.TextField(_("Subscription details, payment schedule, modes of payment etc."), blank=True, null=True)
    membership = models.ForeignKey(Membership, null=False, on_delete=models.PROTECT)
    public = models.BooleanField(_("Is this Subscription public"), default=True)
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='INR', null=False)
    validity_days = models.PositiveIntegerField(_("validity_days"), default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.PROTECT)

    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='allowed_subscriptions', blank=True)
    allowed_groups = models.ManyToManyField(Group, related_name='allowed_subscriptions', blank=True)

    class Meta:
        abstract = False
        app_label = _("membership")
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")


class UserSubscription(BaseLogModelMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subscriptions')
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)

    purchased_on = models.DateTimeField(_("Purchased On"), auto_now_add=True)

    start_date = models.DateTimeField(_("When this subscription starts"), null=True)
    end_date = models.DateTimeField(_("When this subscription ends"), null=True)

    payment_method = models.CharField(_("Payment Method"), max_length=128, null=True, blank=True, db_index=True)
    transaction_id = models.CharField(_("Payment Transaction ID"), max_length=128, null=True, blank=True, db_index=True)

    def is_active(self):
        now = datetime.now()
        return (self.start_date and self.end_date) and (self.start_date < now < self.end_date)
