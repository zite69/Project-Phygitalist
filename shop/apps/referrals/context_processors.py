def user_referral(request):
    """
    Adds `user_referral` to the template context — the logged-in user's
    general referral link, or None for anonymous visitors.
    """
    if not request.user.is_authenticated:
        return {"user_referral": None}

    from shop.apps.referrals.models import Referral

    referral = Referral.objects.filter(user=request.user, label="general").first()
    if not referral:
        referral = Referral.create(user=request.user, redirect_to="/", label="general")

    return {"user_referral": referral}
