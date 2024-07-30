from django.apps import AppConfig
from django.urls import path
from oscar import config

#class MainConfig(AppConfig):
#    default_auto_field = 'django.db.models.BigAutoField'
#    name = 'shop.apps.main'

class MainShop(config.Shop):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.main'

    def get_urls(self):
        urls = super().get_urls()
        urls.pop(1)
        urls.insert(1, path('catalog/', self.catalogue_app.urls))

        return urls

