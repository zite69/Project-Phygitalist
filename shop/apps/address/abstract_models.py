from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core import exceptions
from django.conf import settings
from oscar.apps.address.abstract_models import AbstractAddress as OscarAbstractAddress
from phonenumber_field.modelfields import PhoneNumberField

# Customizing Oscars AbstractAddress class to add the Mx title in the choices
# Will submit this as PR to Oscar, hopefully it will get accepted
class AbstractAddress(OscarAbstractAddress):
    MX = "Mx"
    
    TITLE_CHOICES = tuple([*OscarAbstractAddress.TITLE_CHOICES] + [(MX, _("Mx"))])

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

class AbstractUserAddress(AbstractAddress):
    # From AbstractShippingAddress - oscar
    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        help_text=_("In case we need to call you about your order"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Instructions"),
        help_text=_("Tell us anything we should know when delivering your order."),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("User"),
    )

    #: Whether this address is the default for shipping
    is_default_for_shipping = models.BooleanField(
        _("Default shipping address?"), default=False
    )

    #: Whether this address should be the default for billing.
    is_default_for_billing = models.BooleanField(
        _("Default billing address?"), default=False
    )

    #: We keep track of the number of times an address has been used
    #: as a shipping address so we can show the most popular ones
    #: first at the checkout.
    num_orders_as_shipping_address = models.PositiveIntegerField(
        _("Number of Orders as Shipping Address"), default=0
    )

    #: Same as previous, but for billing address.
    num_orders_as_billing_address = models.PositiveIntegerField(
        _("Number of Orders as Billing Address"), default=0
    )

    #: A hash is kept to try and avoid duplicate addresses being added
    #: to the address book.
    hash = models.CharField(
        _("Address Hash"), max_length=255, db_index=True, editable=False
    )
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Save a hash of the address fields
        """
        # Save a hash of the address fields so we can check whether two
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()

        # Ensure that each user only has one default shipping address
        # and billing address
        self._ensure_defaults_integrity()
        super().save(*args, **kwargs)

    def _ensure_defaults_integrity(self):
        if self.is_default_for_shipping:
            self.__class__._default_manager.filter(
                user=self.user, is_default_for_shipping=True
            ).update(is_default_for_shipping=False)
        if self.is_default_for_billing:
            self.__class__._default_manager.filter(
                user=self.user, is_default_for_billing=True
            ).update(is_default_for_billing=False)

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("User address")
        verbose_name_plural = _("User addresses")
        ordering = ["-num_orders_as_shipping_address"]
        unique_together = ("user", "hash")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        qs = self.__class__.objects.filter(user=self.user, hash=self.generate_hash())
        if self.id:
            qs = qs.exclude(id=self.id)
        if qs.exists():
            raise exceptions.ValidationError(
                {"__all__": [_("This address is already in your address book")]}
            )


    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


class AbstractOrganizationAddress(AbstractAddress):
    organization_name = models.CharField(_("Organization Name"), max_length=255, blank=False)

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("Organization Address")
        verbose_name_plural = _("Organization Addresses")

