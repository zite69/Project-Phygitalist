from django import template
from urllib.parse import quote_plus, urlencode, urlparse, urlunparse, parse_qs

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
        return request.build_absolute_uri(redirect_to) if request else redirect_to

    from shop.apps.referrals.models import Referral

    # One persistent code per user — keyed on user+label only so the same
    # code is reused regardless of which URL is being shared.
    referral, _ = Referral.objects.get_or_create(
        user=request.user,
        label="personal",
        defaults={"redirect_to": "/"},
    )
    parsed = urlparse(redirect_to)
    params = parse_qs(parsed.query)
    params['r'] = [referral.code]
    new_query = urlencode(params, doseq=True)
    relative = urlunparse(parsed._replace(query=new_query))
    return request.build_absolute_uri(relative)


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
