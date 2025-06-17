from django.urls import path
from django.apps import apps
from oscar import config
from oscar.core.loading import get_class
import logging
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

logger = logging.getLogger("shop.apps.main")

class MainShop(config.Shop):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.main'

    def ready(self):
        super().ready()

        from .views import test, fivehundred

        self.test_view = test
        self.fivehundred = fivehundred

    def get_urls(self):
        urls = super().get_urls()
        urls.pop(0) #Remove the RedirectView that redirects the home page, Our CMS will handle this view
        #urls.pop(0) #Remove the url spelled /catalogue/ and replace with /catalog/ below
        # urls.pop(4) #Remove the dashboard urls because the CMS Apphook will handle this
        # urls.insert(0, path('catalog/', self.catalogue_app.urls))
        # urls.insert(0, path('test/', self.test_view))
        # urls.insert(0, path('error/', self.fivehundred))

        return urls

