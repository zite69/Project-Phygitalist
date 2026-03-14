import oscar.apps.dashboard.orders.apps as apps


class OrdersDashboardConfig(apps.OrdersDashboardConfig):
    name = 'shop.apps.catalogue_dashboard.dashboard.orders.dashboard.orders'

    def ready(self):
        super().ready()
        from .views import OrderDetailView
        self.order_detail_view = OrderDetailView
