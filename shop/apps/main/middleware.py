from django.conf import settings
from django.middleware.common import MiddlewareMixin
from django.contrib.sites.models import Site
from django.urls import include
from django.apps import apps
import logging
from shop.apps.invitation.models import Invitation, InvitationCode

logger = logging.getLogger("shop.apps.main")

class DynamicSiteMiddleware(MiddlewareMixin):
    """
    Make the domains available on request.site
    and set settings.SITE_ID to the correct Site object
    """
    def process_request(self, request):
        # logger.debug(request.get_host())
        # host = request.get_host().split(":")[0]
        host = request.get_host()
        try:
            current_site = Site.objects.get(domain=host)
            # logger.debug(f"Got site: {current_site}")
        except Site.DoesNotExist:
            current_site = Site.objects.get(id=settings.DEFAULT_SITE_ID)
            logger.debug(f"Got default site: {current_site}")

        request.site = current_site
        settings.SITE_ID = current_site.id
        if current_site.id == settings.SELLER_SITE_ID:
            request.urlconf = 'shop.urls_seller'
        else:
            request.urlconf = 'shop.urls'

        response = self.get_response(request)
        return response

class Zite69Middleware(MiddlewareMixin):
    """
    All in one middleware for the site - Handles lookup of invitations and referrals in the query parameters
    """
    def __init__(self, get_response):
        super().__init__(get_response)
