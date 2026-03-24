import oscar.apps.dashboard.apps as apps
from django.urls import reverse_lazy


class DashboardConfig(apps.DashboardConfig):
    name = 'shop.apps.dashboard'
    login_url = reverse_lazy("account_login")
