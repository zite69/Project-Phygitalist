from shop.apps.user.models import User
from shop.apps.registration.models import SellerProduct, SellerRegistration
from django.contrib.sessions.models import Session
from django.db.models import Q
from django.conf import settings

def run(*args):
    SellerProduct.objects.all().delete()
    SellerRegistration.objects.all().delete()
    for u in User.objects.filter(~Q(username='system') & ~Q(username='arun') & ~Q(username=settings.ZITE69_SU_USERNAME)
                & ~Q(username__startswith='seller')):
        u.bankaccount_set.all().delete()
        u.seller.pickup_addresses.all().delete()
        u.seller.delete()
        u.save()
    Session.objects.all().delete()
