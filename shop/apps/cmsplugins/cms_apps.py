from django.apps import apps
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from oscar.apps.dashboard.apps import DashboardConfig

@apphook_pool.register
class DashboardAppHook(CMSApp):
    app_name = "dashboard"
    name = "Oscar-CMS Dashboard"

    def get_urls(self, page=None, language=None, **kwargs):
        # dashconf = DashboardConfig(app_name="dashboard", app_module="dashboard")
        dashboard = apps.get_app_config("dashboard")
        return [dashboard.urls[0]]
