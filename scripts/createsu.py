from shop.apps.user.models import User
from django.conf import settings

def run(*args):
    User.objects.create_superuser(settings.ZITE69_SU_USERNAME, settings.ZITE69_SU_PASSWORD)
