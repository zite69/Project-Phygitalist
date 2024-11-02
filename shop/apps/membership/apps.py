from django.apps import AppConfig
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig

class MembershipConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.membership'
    label = 'membership'
    verbose_name = _("membership")
    namespace = 'membership'

    def ready(self):
        super().ready()
        from shop.apps.membership.views import MembershipCreateView, MembershipDetailView, SubscriptionCreateView, SubscriptionDetailView

        self.member_create = MembershipCreateView
        self.member_detail = MembershipDetailView
        self.subscription_create = SubscriptionCreateView
        self.subscription_detail = SubscriptionDetailView

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('create/', self.member_create.as_view(), name="create"),
            path("<int:pk>", self.member_detail.as_view(), name="detail"),
            path("<int:pk>/subscriptions/create", self.subscription_create.as_view(), name="subscription-create"),
            path("<int:pk>/subscriptions/<int:subscription_pk>", self.subscription_detail.as_view(), name="subscription-detail")
        ]

        return urls
