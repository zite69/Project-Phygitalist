from django.apps import AppConfig
from oscar import config
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig

class OtpConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.otp'
    label = "otp"
    verbose_name = _("Otp")

    namespace = "otp"

    def ready(self):
        super().ready()
        from .views import RequestOtpView, OtpLoginView

        self.request_view = RequestOtpView
        self.login_view = OtpLoginView
    
    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('request/', self.request_view.as_view(), name="request"),
            path('login/', self.login_view.as_view(), name="login")
        ]

        return urls
