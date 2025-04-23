from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
from functools import lru_cache

@lru_cache()
def get_site_base_uri(site_id=settings.SITE_ID):
    site = Site.objects.get(id=site_id)
    protocol = 'https' if settings.USE_HTTPS else 'http'
    return f"{protocol}://{site.domain}"

def get_absolute_url(site_id=settings.SITE_ID, view_name=""):
    sbu = get_site_base_uri(site_id=site_id)
    urlconf = 'shop.urls' if site_id == settings.DEFAULT_SITE_ID else 'shop.urls_seller'
    if view_name == "":
        return sbu
    else:
        return f"{sbu}{reverse(view_name, urlconf=urlconf)}"
