from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from shop.apps.membership.models import Membership, Subscription
from shop.apps.membership.forms import CreateMembershipForm

class MembershipCreateView(CreateView):
    model = Membership
    form_class = CreateMembershipForm

class MembershipDetailView(DetailView):
    model = Membership

class SubscriptionCreateView(CreateView):
    model = Subscription

class SubscriptionDetailView(DetailView):
    model = Subscription
    pk_url_kwarg = 'subscription_id'
