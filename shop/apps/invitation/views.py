from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import InvitationForm, InviteForm
from .models import Invitation

class InvitationsList(LoginRequiredMixin, ListView, FormMixin):
    form_class = InvitationForm
    model = Invitation
    paginate_by = 10
