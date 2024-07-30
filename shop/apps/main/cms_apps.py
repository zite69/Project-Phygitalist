from django.apps import apps
from cms.apphook_pool import apphook_pool, CMSApp
from django.utils.translation import gettext_lazy as _

class ShopApphook(CMSApp):
    name = _("Shop")
    #urls = [apps.get_app_config('main').urls[0]]
    urls = []

apphook_pool.register(ShopApphook)