from django.urls import path
from django.apps import apps
from oscar import config
from oscar.core.loading import get_class
import logging
import os
import re
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

logger = logging.getLogger("shop.apps.main")


def _inline_mjml_includes(mjml_source, base_dir, visited=None):
    """
    Recursively replace <mj-include path="..."> tags with the actual file
    contents so the MJML CLI (running in stdin mode) never has to resolve
    file paths itself.
    """
    if visited is None:
        visited = set()

    def replace_include(match):
        path = match.group(1)
        full_path = os.path.join(base_dir, path)
        if full_path in visited:
            return ''
        visited.add(full_path)
        try:
            with open(full_path) as f:
                content = f.read()
            return _inline_mjml_includes(content, base_dir, visited)
        except FileNotFoundError:
            logger.warning(f'MJML include not found: {full_path}')
            return ''

    return re.sub(r'<mj-include\s+path="([^"]+)"\s*/>', replace_include, mjml_source)


class MainShop(config.Shop):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.main'

    def ready(self):
        super().ready()

        from .views import test, fivehundred
        from django.conf import settings
        import mjml.tools as mjml_tools

        self.test_view = test
        self.fivehundred = fivehundred

        from mjml.templatetags.mjml import MJMLRenderNode
        from mjml.tools import mjml_render as _original_mjml_render
        from django.template import engines

        _original_node_render = MJMLRenderNode.render

        def _patched_node_render(self, context):
            # Step 1: render Django template nodes inside {% mjml %}...{% endmjml %}
            mjml_source = self.nodelist.render(context)
            # Step 2: inline mj-include files from disk (replaces <mj-include path="..."> with file content)
            mjml_source = _inline_mjml_includes(mjml_source, str(settings.BASE_DIR))
            # Step 3: re-render the inlined content so Django variables/tags inside
            #         the .mjml file ({{ otp }}, {% site_url %}, {% if %}, etc.) are resolved
            mjml_source = engines['django'].from_string(mjml_source).render(context.flatten())
            # Step 4: pass clean MJML to the CLI
            return _original_mjml_render(mjml_source)

        MJMLRenderNode.render = _patched_node_render

    def get_urls(self):
        urls = super().get_urls()
        urls.pop(0) #Remove the RedirectView that redirects the home page, Our CMS will handle this view
        #urls.pop(0) #Remove the url spelled /catalogue/ and replace with /catalog/ below
        # urls.pop(4) #Remove the dashboard urls because the CMS Apphook will handle this
        # urls.insert(0, path('catalog/', self.catalogue_app.urls))
        # urls.insert(0, path('test/', self.test_view))
        # urls.insert(0, path('error/', self.fivehundred))

        return urls

