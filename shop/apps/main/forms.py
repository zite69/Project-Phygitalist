from djangocms_form_builder import actions
from django.utils.translation import gettext_lazy as _

@actions.register
class AddToMailingList(actions.FormAction):
    verbose_name = _("Add to mailing list")

    def execute(self, form, request):
        print(form)
        print(request)
