from django.utils.translation import gettext_lazy as _
from django.urls import include, path, re_path
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class SellerConfig(OscarConfig):
    label = "seller"
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.seller'
    verbose_name = _("Seller")

    namespace = "seller"

    def ready(self) -> None:
        super().ready()
    
        self.profile_view = get_class("seller.views", "ProfileView")
        self.shop_view = get_class("seller.views", "ShopView")


    def get_urls(self):
        urls = super().get_urls()

        urls += [
            path("", self.shop_view.as_view(), name="index"),
            path("profile/", self.profile_view.as_view(), name="profile")
        ]

