from django.apps import AppConfig
from django.urls import path
from djangocms_form_builder import verbose_name
from oscar.core.application import OscarConfig
from django.utils.translation import gettext_lazy as _

class InvitationConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.invitation'
    label = 'invitation'
    namespace = 'invitation'
    verbose_name = _("Invitation")

    def ready(self):
        super().ready()
        from .views import InvitationsList

        self.invitations_list = InvitationsList


    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('', self.invitations_list.as_view(), name='index')
        ]
        return urls
