from django import template
from urllib.parse import quote_plus

register = template.Library()


@register.simple_tag(takes_context=True)
def referral_share_url(context, redirect_to):
    """
    Returns the referral redirect URL for the current user pointing at
    `redirect_to`. If the user is not authenticated, returns `redirect_to`
    unchanged so the template still works for anonymous visitors.

    Usage:
        {% referral_share_url product.get_absolute_url as share_url %}
    """
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return redirect_to

    from shop.apps.referrals.models import Referral

    referral = Referral.create(
        user=request.user,
        redirect_to=redirect_to,
        label="share",
    )
    return referral.url


@register.simple_tag
def facebook_share(url):
    return f"https://www.facebook.com/sharer/sharer.php?u={quote_plus(url)}"


@register.simple_tag
def twitter_share(url, text=""):
    encoded_url = quote_plus(url)
    encoded_text = quote_plus(text)
    return f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_text}"


@register.simple_tag
def whatsapp_share(url, text=""):
    message = quote_plus(f"{text} {url}".strip())
    return f"https://wa.me/?text={message}"
