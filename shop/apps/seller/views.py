from typing import Any
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.views.generic import DetailView
from django.shortcuts import redirect
from shop.apps.seller.models import Seller
from shop.apps.user.models import Profile
from shop.apps.seller.forms import SellerRegistrationForm
#from pinax.referrals.models import Referral
import logging

logger = logging.getLogger('shop.apps.seller')

class ProfileView(DetailView):
    model = Profile

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            profile = Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            redirect("seller:profile_create")

class ProfileCreate(CreateView):
    model = Profile

    def form_valid(self, form):
        form.instance.user = self.request.user
        referral_response = Referral.record_response(self.request, "REGISTER")
        logger.info(f"Create Profile: user: {self.request.user}, referral_response: {referral_response}")
        logger.info(f"referred by: {referral_response.referral.user}")
        if referral_response:
            form.instance.referred_by = referral_response.referral.user
        return super().form_valid(form)

class RegisterView(FormView):
    form_class = SellerRegistrationForm

    def form_valid(self, form: Any) -> HttpResponse:
        return super().form_valid(form)

class ShopView(DetailView):
    model = Seller
