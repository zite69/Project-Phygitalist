from django.conf import settings
from django.contrib.sites.models import Site
from functools import lru_cache

@lru_cache()
def get_site_base_uri(site_id=settings.SITE_ID):
    site = Site.objects.get(id=site_id)
    protocol = 'https' if settings.USE_HTTPS else 'http'
    return f"{protocol}://{site.domain}"


