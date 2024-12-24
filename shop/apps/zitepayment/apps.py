from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig

class ZitepaymentConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.zitepayment'
    label = 'zitepayment'
    verbose_name = _("Zite Payment")
    namespace = 'zitepayment'

    def ready(self):
        return super().ready()

    def get_urls(self):
        return super().get_urls()
