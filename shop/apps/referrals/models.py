from inspect import getfullargspec
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone
import random

def generate_code(referral_class, referral):
    def _generate_code():
        t = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890"
        return "".join([random.choice(t) for i in range(40)])
    code = _generate_code()
    while referral_class.objects.filter(code=code).exists():
        code = _generate_code()
    return code

def filter_responses(user=None, referral=None):
    responses = ReferralResponse.objects.all()
    if user:
        responses = responses.filter(referral__user=user)
    if referral:
        responses = responses.filter(referral=referral)
    return responses.order_by("-created_at")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    #return request.META.get(settings.IP_ADDRESS_META_FIELD, "HTTP_X_FORWARDED_FOR")

class Referral(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="referral_codes",
        null=True,
        blank=True
    )
    label = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=40, unique=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    redirect_to = models.CharField(max_length=512)
    target_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey(
        ct_field="target_content_type",
        fk_field="target_object_id"
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.user:
            return f"{self.user} ({self.code})"
        else:
            return self.code

    @classmethod
    def for_request(cls, request):
        cookie = request.COOKIES.get("pinax-referral")
        if cookie:
            code, session_key = cookie.split(":")
            try:
                return Referral.objects.get(code=code)
            except Referral.DoesNotExist:
                pass

    @property
    def url(self):
        path = reverse("pinax_referrals:process_referral", kwargs={"code": self.code})
        domain = Site.objects.get_current().domain
        protocol = "https" if settings.USE_HTTPS else "http"
        return f"{protocol}://{domain}{path}"

    @property
    def response_count(self):
        return self.responses.filter(action="RESPONDED").count()

    def save(self, *args, **kwargs):
        if not self.code:
            func_args = [Referral] if len(getfullargspec(generate_code).args) == 1 else [Referral, self]
            self.code = generate_code(*func_args)
        return super().save(*args, **kwargs)

    @classmethod
    def create(cls, redirect_to, user=None, label="", target=None):
        if target:
            obj, _ = cls.objects.get_or_create(
                user=user,
                redirect_to=redirect_to,
                label=label,
                target_content_type=ContentType.objects.get_for_model(target),
                target_object_id=target.pk
            )
        else:
            obj, _ = cls.objects.get_or_create(
                user=user,
                label=label,
                redirect_to=redirect_to,
            )

        return obj

    @classmethod
    def record_response(cls, request, action_string, target=None):
        referral = cls.referral_for_request(request)
        if referral:
            return referral.respond(request, action_string, target=target)

    @classmethod
    def referral_responses_for_request(cls, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            qs = ReferralResponse.objects.filter(user=request.user)
        else:
            qs = ReferralResponse.objects.filter(session_key=request.session.session_key)

        return qs.order_by("-created_at")

    @classmethod
    def referral_for_request(cls, request):
        responses = cls.referral_responses_for_request(request)
        if responses:
            try:
                return responses[0].referral
            except IndexError:
                pass

    def link_responses_to_user(self, user, session_key):
        for response in self.responses.filter(session_key=session_key, user__isnull=True):
            response.user = user
            response.save()
            user_linked_to_response.send(sender=self, response=response)

    def respond(self, request, action_string, user=None, target=None):
        if user is None:
            if request.user.is_authenticated:
                user = request.user
            else:
                user = None

        ip_address = get_client_ip(request)

        kwargs = {
            "referral": self,
            "session_key": request.session.session_key,
            "ip_address": ip_address,
            "action": action_string,
            "user": user,
            "http_referrer": request.META.get("HTTP_REFERER", ""),
        }
        if target:
            kwargs.update({"target": target})

        return ReferralResponse.objects.create(**kwargs)

    def filtered_responses(self):
        return filter_responses(
            referral=self
        )


class ReferralResponse(models.Model):

    referral = models.ForeignKey(Referral, related_name="responses", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    ip_address = models.CharField(max_length=265)
    action = models.CharField(max_length=128)
    http_referrer = models.CharField(max_length=1024, blank=True)

    target_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey(
        ct_field="target_content_type",
        fk_field="target_object_id"
    )

    created_at = models.DateTimeField(default=timezone.now)
