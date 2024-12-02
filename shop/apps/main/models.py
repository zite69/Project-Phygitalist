from django.db import models
from django.db.models import Index
from django.utils.translation import gettext_lazy as _
from djangocms_form_builder.models import MAX_LENGTH
from localflavor.in_.models import INStateField
from localflavor.in_.in_states import STATE_CHOICES
from django.contrib.contenttypes.models import ContentType

class BaseLogModelMixin(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def _get_logs(self):
        '''Gets the log entries related to this object.
        Getter to be used as property instead of GenericRelation'''
        #my_class = self.__class__
        ct = ContentType.objects.get_for_model(self.__class__)
        object_logs = ct.logentry_set.filter(object_id=self.id)
        return object_logs

    logs = property(_get_logs)

class State(models.Model):
    code = models.CharField(_("Indian State 2 character code"), max_length=2, choices=STATE_CHOICES)
    name = models.CharField(_("State Name"), max_length=50)

    class Meta:
        indexes = [
            Index(fields=['code', 'name'])
        ]

class Postoffice(models.Model):
    office = models.CharField(_("Post Office Name"), max_length=64, db_index=True)
    pincode = models.CharField(_("PIN Code"), max_length=6, db_index=True)
    state = models.ForeignKey(State, on_delete=models.PROTECT)

    class Meta:
        indexes = [
            Index(fields=['office', 'pincode'])
        ]
