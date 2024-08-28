from django.urls import path
from oscar import config
import logging
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .utils.email import send_waitlist_welcome

logger = logging.getLogger("shop.apps.main")

class MainShop(config.Shop):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.main'

    def ready(self):
        super().ready()

        from djangocms_form_builder import actions
        from djangocms_form_builder.models import FormEntry

        @actions.register
        class AddToMailingList(actions.FormAction):
            verbose_name = _("Add to mailing list")

            def execute(self, form, request):
                email = form.cleaned_data['email']
                logger.debug(f"In AddToMailingList execute got email: {email}")
                getonwaitlist = FormEntry.objects.filter(form_name__iexact='getonwaitlist').filter(entry_data__email=email)
                if getonwaitlist:
                    logger.debug("User already in the waitlist")
                    messages.error(request, "You have already added your name to the waitlist. Please wait for your confirmation email")
                else:
                    count = send_waitlist_welcome(form.cleaned_data['email'])
                    logger.debug(f"Got response back from send email call: {count}")
                    messages.success(request, "You have been added to the waiting list. Please expect an email from us soon!")

        #logger.warn("Inside FormAction execute")
        #logger.debug(actions._action_registry)

    def get_urls(self):
        urls = super().get_urls()
        urls.pop(1)
        urls.insert(1, path('catalog/', self.catalogue_app.urls))

        return urls

