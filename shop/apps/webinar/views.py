from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import RegistrationForm

class CreateRegistrationView(CreateView):
    form_class = RegistrationForm
    template_name = 'webinar.html'
    success_url = reverse_lazy('webinarthanks')
