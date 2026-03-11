COOKIE_NAME = "pinax-referral"


class ReferralCookieMiddleware:
    """
    Attaches the current Referral (if any) to the request object so views
    and templates can access it cheaply without repeated DB lookups.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from shop.apps.referrals.models import Referral

        request.referral = Referral.for_request(request)
        return self.get_response(request)
