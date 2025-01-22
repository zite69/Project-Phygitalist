import oscar.apps.dashboard.partners.apps as apps

class PartnersDashboardConfig(apps.PartnersDashboardConfig):
    name = 'shop.apps.partners_dashboard.dashboard.partners'

    def ready(self):
        from .views import (PartnerListView, PartnerCreateView, PartnerManageView, PartnerDeleteView)
        ret = super().ready()
        self.list_view = PartnerListView
        self.create_view = PartnerCreateView
        self.manage_view = PartnerManageView
        self.delete_view = PartnerDeleteView

        return ret
