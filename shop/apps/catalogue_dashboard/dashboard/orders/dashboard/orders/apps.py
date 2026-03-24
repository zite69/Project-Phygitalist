import oscar.apps.dashboard.orders.apps as apps
from django.urls import reverse_lazy


class OrdersDashboardConfig(apps.OrdersDashboardConfig):
    name = 'shop.apps.catalogue_dashboard.dashboard.orders.dashboard.orders'
    login_url = reverse_lazy("account_login")

    def ready(self):
        super().ready()
        from .views import OrderDetailView, OrderListView
        self.order_detail_view = OrderDetailView
        self.order_list_view = OrderListView
