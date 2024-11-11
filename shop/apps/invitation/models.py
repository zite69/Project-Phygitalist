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

class SignupCode(models.Model):
    class AlreadyExists(Exception):
        pass

    class InvalidCode(Exception):
        pass

    code = models.CharField(_("code"), max_length=64, unique=True)
    max_uses = models.PositiveIntegerField(_("max uses"), default=1)
    expiry = models.DateTimeField(_("expiry"), null=True, blank=True)
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    sent = models.DateTimeField(_("sent"), null=True, blank=True)
    created = models.DateTimeField(_("created"), default=timezone.now, editable=False)
    use_count = models.PositiveIntegerField(_("use count"), editable=False, default=0)
    phone = PhoneNumberField(verbose_name=_("Phone"), db_index=True, blank=True, null=True)

    class Meta:
        verbose_name = _("signup code")
        verbose_name_plural = _("signup codes")


    def __str__(self):
        if self.email:
            return "{0} [{1}]".format(self.email, self.code)
        elif self.phone:
            return "{0} [{1}]".format(self.phone, self.code)
        return str(self.code)

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

    def calculate_use_count(self):
        self.use_count = self.signupcoderesult_set.count()
        self.save()

    def use(self, user):
        """
        Add a SignupCode result attached to the given user.
        """
        result = SignupCodeResult()
        result.signup_code = self
        result.user = user
        result.save()
        signup_code_used.send(sender=result.__class__, signup_code_result=result)

    def send(self, **kwargs):
        if settings.USE_HTTPS:
            protocol = "https"
        else:
            protocol = "http"

        current_site = kwargs["site"] if "site" in kwargs else Site.objects.get_current()
        if "signup_url" not in kwargs:
            signup_url = "{0}://{1}{2}?{3}".format(
                protocol,
                current_site.domain,
                reverse("account_signup"),
                urlencode({"code": self.code})
            )
        else:
            signup_url = kwargs["signup_url"]
        ctx = {
            "signup_code": self,
            "current_site": current_site,
            "signup_url": signup_url,
        }
        ctx.update(kwargs.get("extra_ctx", {}))
        send_email_invite(self.email, ctx)
        self.sent = timezone.now()
        self.save()
        signup_code_sent.send(sender=SignupCode, signup_code=self)

class SignupCodeResult(models.Model):

    signup_code = models.ForeignKey(SignupCode, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)

    def save(self, **kwargs):
        super(SignupCodeResult, self).save(**kwargs)
        self.signup_code.calculate_use_count()

class JoinInvitation(models.Model):

    STATUS_SENT = 1
    STATUS_ACCEPTED = 2
    STATUS_JOINED_INDEPENDENTLY = 3

    INVITE_STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_JOINED_INDEPENDENTLY, "Joined Independently")
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invites_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name="invites_received"
    )
    message = models.TextField(null=True)
    sent = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=INVITE_STATUS_CHOICES)
    signup_code = models.OneToOneField(SignupCode, on_delete=models.CASCADE)

    def to_user_email(self):
        return self.signup_code.email

    def accept(self, user):
        self.to_user = user
        self.status = JoinInvitation.STATUS_ACCEPTED
        self.save()
        self.from_user.invitationstat.increment_accepted()
        invite_accepted.send(sender=JoinInvitation, invitation=self)

    @classmethod
    def process_independent_joins(cls, user, email):
        invites = cls.objects.filter(
            to_user__isnull=True,
            signup_code__email=email
        )
        for invite in invites:
            invite.to_user = user
            invite.status = cls.STATUS_JOINED_INDEPENDENTLY
            invite.save()
            joined_independently.send(sender=cls, invitation=invite)

    @classmethod
    def invite(cls, from_user, to_email, message=None, send=True):
        if not from_user.invitationstat.can_send():
            raise NotEnoughInvitationsError()

        signup_code = SignupCode.create(
            email=to_email,
            inviter=from_user,
            expiry=settings.PINAX_INVITATIONS_DEFAULT_EXPIRATION,
            check_exists=False  # before we are called caller must check for existence
        )
        signup_code.save()
        join = cls.objects.create(
            from_user=from_user,
            message=message,
            status=JoinInvitation.STATUS_SENT,
            signup_code=signup_code
        )

        def send_invite(*args, **kwargs):
            signup_code.send(*args, **kwargs)
            InvitationStat.objects.filter(user=from_user).update(
                invites_sent=models.F("invites_sent") + 1
            )
            invite_sent.send(sender=cls, invitation=join)
        if send:
            send_invite()
        else:
            join.send_invite = send_invite
        return join


class InvitationStat(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    invites_sent = models.IntegerField(default=0)
    invites_accepted = models.IntegerField(default=0)

    def increment_accepted(self):
        self.invites_accepted += 1
        self.save()


    def can_send(self):
        """
        Return True if an invite can be sent.
        """
        return True


    can_send.boolean = True

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
