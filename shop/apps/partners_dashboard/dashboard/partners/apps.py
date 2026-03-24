import oscar.apps.dashboard.partners.apps as apps
from django.urls import reverse_lazy

class PartnersDashboardConfig(apps.PartnersDashboardConfig):
    name = 'shop.apps.partners_dashboard.dashboard.partners'
    login_url = reverse_lazy("account_login")

    def ready(self):
        from .views import (PartnerListView, PartnerCreateView, PartnerManageView, PartnerDeleteView)
        ret = super().ready()
        self.list_view = PartnerListView
        self.create_view = PartnerCreateView
        self.manage_view = PartnerManageView
        self.delete_view = PartnerDeleteView

        return ret
