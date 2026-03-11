from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from shop.apps.referrals.models import Referral, ReferralResponse, filter_responses

COOKIE_NAME = "pinax-referral"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


class ProcessReferralView(View):
    """
    Records a referral visit, sets the tracking cookie, then redirects
    to the URL the referral points at.
    """

    def get(self, request, code):
        try:
            referral = Referral.objects.get(code=code)
        except Referral.DoesNotExist:
            return redirect("/")

        if referral.expired_at and referral.expired_at < timezone.now():
            return redirect(referral.redirect_to or "/")

        # Ensure session exists so we have a key
        if not request.session.session_key:
            request.session.create()

        referral.respond(request, "RESPONDED")

        response = redirect(referral.redirect_to or "/")
        response.set_cookie(
            COOKIE_NAME,
            f"{referral.code}:{request.session.session_key}",
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )
        return response


class ReferralDashboardView(LoginRequiredMixin, TemplateView):
    """Shows a user their referral link and who they have referred."""

    template_name = "referrals/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create a general referral link for the user
        general_referral = Referral.objects.filter(user=user, label="general").first()
        if not general_referral:
            general_referral = Referral.create(
                user=user, redirect_to="/", label="general"
            )

        ctx["referral"] = general_referral
        ctx["responses"] = filter_responses(user=user)
        ctx["referred_users"] = (
            ReferralResponse.objects.filter(
                referral__user=user,
                action="RESPONDED",
                user__isnull=False,
            )
            .select_related("user")
            .order_by("-created_at")
        )
        return ctx


class ReferralLinkForUrlView(LoginRequiredMixin, View):
    """
    Returns (or creates) a referral link for a given target URL.
    Called via AJAX from the product detail page share buttons.
    """

    def get(self, request):
        redirect_to = request.GET.get("url", "/")
        referral = Referral.create(
            user=request.user, redirect_to=redirect_to, label="share"
        )
        return JsonResponse({"referral_url": referral.url})
