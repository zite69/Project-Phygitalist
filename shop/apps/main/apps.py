from django.urls import path
from oscar import config
import logging
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("shop.apps.main")

class MainShop(config.Shop):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.main'

    def ready(self):
        super().ready()

        from djangocms_form_builder import actions
        @actions.register
        class AddToMailingList(actions.FormAction):
            verbose_name = _("Add to mailing list")

            def execute(self, form, request):
                logger.warn("Called from Add to mailing list FormAction")
                logger.warn(form)
                logger.debug(request)

        logger.warn("Inside FormAction execute")
        logger.debug(actions._action_registry)

    def get_urls(self):
        urls = super().get_urls()
        urls.pop(1)
        urls.insert(1, path('catalog/', self.catalogue_app.urls))

        return urls

