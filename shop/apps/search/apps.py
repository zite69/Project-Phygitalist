# from django.apps import AppConfig
from oscar.core.application import OscarConfig
from django.conf import settings
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _


class SearchConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.search'
    label = 'search'
    namespace = 'search'
    verbose_name = _("Catalog Search")

    def ready(self):
        super().ready()
        from shop.apps.search.views import SearchView

        self.search_view = SearchView.as_view()

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('', self.search_view, name='search')
        ]
        return urls
