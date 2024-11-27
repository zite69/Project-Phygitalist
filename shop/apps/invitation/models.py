from re import I
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.shortcuts import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.auth.models import Permission

#from pinax.invitations import models as pimodels
#from account.models import SignupCodeResult
from phonenumber_field.modelfields import PhoneNumberField
from typing import Self
from shop.apps.invitation.signals import signup_code_used, signup_code_sent, invite_sent, invite_accepted, joined_independently
from shop.apps.main.utils.email import send_email_invite
from shop.apps.main.models import BaseLogModelMixin

import functools
import operator
import hashlib
import random
import datetime
import pytz

class InvitationCode(BaseLogModelMixin):
    class AlreadyExists(Exception):
        pass

    class InvalidCode(Exception):
        pass

    STATUS_SENT = 'S'
    STATUS_ACCEPTED = 'A'
    STATUS_JOINED_INDEPENDENTLY = 'I'

    STATUS_CHOICES = (
        (STATUS_SENT, _("Invite Sent")),
        (STATUS_ACCEPTED, _("Invite Accepted")),
        (STATUS_JOINED_INDEPENDENTLY, _("Invite Not Used"))
    )

    code = models.CharField(_("Invitation Code"), max_length=64, db_index=True, unique=True, blank=False, null=False)
    expiry = models.DateTimeField(verbose_name=_("Expiry Date"), null=True)
    sent_on = models.DateTimeField(_("Sent On"), null=True)
    email = models.EmailField(_("Email address"), db_index=True, max_length=254, null=True)
    phone = PhoneNumberField(_("Phone Number"), region='IN', db_index=True, null=True)
    status = models.CharField(_("Invitation Code Status"), max_length=1, choices=STATUS_CHOICES, db_index=True, default=STATUS_SENT)
    invitation = models.ForeignKey('Invitation', on_delete=models.CASCADE, related_name='codes')
    short_url = models.URLField(_("Shortened URL"), db_index=True, null=False, unique=True)


    @classmethod
    def exists(cls, code=None, email=None, phone=None):
        checks = []
        if code:
            checks.append(Q(code=code))
        if email:
            checks.append(Q(email=email))
        if phone:
            checks.append(Q(phone=phone))
        if not checks:
            return False
        return cls._default_manager.filter(functools.reduce(operator.or_, checks)).exists()

    @classmethod
    def generate_signup_code_token(cls, extra=None) -> str:
        if extra is None:
            extra = []
        bits = extra + [str(random.SystemRandom().getrandbits(512))]
        return hashlib.sha256("".join(bits).encode("utf-8")).hexdigest()

    @classmethod
    def create(cls, **kwargs) -> Self:
        email, phone, code = kwargs.get("email"), kwargs.get("phone"), kwargs.get("code")
        if kwargs.get("check_exists", True) and (cls.exists(code=code, email=email) or cls.exists(code=code, phone=phone)):
            raise cls.AlreadyExists()
        expiry = timezone.now() + datetime.timedelta(hours=kwargs.get("expiry", 24))
        if not code:
            code = cls.generate_signup_code_token([email, phone])
        params = {
                    "code": code,
                    "max_uses": kwargs.get("max_uses", 0),
                    "expiry": expiry,
                    "inviter": kwargs.get("inviter"),
                    "notes": kwargs.get("notes", ""),
                    "url": kwargs.get("url", "")
                }
        if email:
            params['email'] = email
        if phone:
            params['phone'] = phone

        return cls(**kwargs)

    @classmethod
    def check_code(cls, code):
        try:
            signup_code = cls._default_manager.get(code=code)
        except cls.DoesNotExist:
            raise cls.InvalidCode()
        else:
            if signup_code.max_uses and signup_code.max_uses <= signup_code.use_count:
                raise cls.InvalidCode()
            else:
                if signup_code.expiry and timezone.now() > signup_code.expiry:
                    raise cls.InvalidCode()
                else:
                    return signup_code

class Invitation(BaseLogModelMixin):
    TYPE_SELLER = 'S'
    TYPE_CEO = 'C'

    INVITE_TYPE_CHOICES = (
        (TYPE_SELLER, _("Invite Seller")),
        (TYPE_CEO, _("Invite CEO"))
    )

    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(_("Email Address"), max_length=254, db_index=True, null=True)
    phone = PhoneNumberField(_("Phone Number"), db_index=True, region='IN', null=True)
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invited_by', null=True)
    invite_type = models.CharField(_("Invite Type"), max_length=1, db_index=True, choices=INVITE_TYPE_CHOICES, default=TYPE_SELLER)
    local_url = models.URLField(_("Local path to handle invitation"))
    #Optionally what permissions do we give the invited user
    permissions = models.ManyToManyField(Permission, related_name='invitations')
    #Configuration options for the new user
    configuration = models.JSONField(_("Invitation Configuration"), null=True)

    class Meta:
        permissions = [
            (
                "invite_seller",
                "Invite someone to become a Premium Seller using their email address and/or phonenumber"
            ),
            (
                "invite_ceo",
                "Invite someone to become a CEO (Community Exchange Officer) of the site"
            )
        ]
