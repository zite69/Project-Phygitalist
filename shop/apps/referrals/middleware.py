REFERRAL_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


class ReferralCookieMiddleware:
    """
    Two jobs:
    1. Attaches the current Referral (if any) to request.referral so views
       and templates can access it without repeated DB lookups.
    2. If a ?r=<code> query parameter is present, records a ReferralResponse
       and sets the tracking cookie, so any page link can carry a referral.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        from shop.apps.referrals.models import Referral
        from django.utils import timezone

        request.referral = Referral.for_request(request)

        referral_from_param = None
        code = request.GET.get('r')
        if code:
            try:
                referral = Referral.objects.get(code=code)
                if not (referral.expired_at and referral.expired_at < timezone.now()):
                    referral_from_param = referral
            except Referral.DoesNotExist:
                pass

        if referral_from_param and not request.session.session_key:
            request.session.create()

        response = self.get_response(request)

        if referral_from_param:
            referral_from_param.respond(request, "RESPONDED")
            response.set_cookie(
                settings.REFERRAL_COOKIE_NAME,
                f"{referral_from_param.code}:{request.session.session_key}",
                max_age=REFERRAL_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
            )
            request.referral = referral_from_param

        return response
