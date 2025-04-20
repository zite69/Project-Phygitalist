from django.conf import settings as django_settings


def settings(request):
    return {
        'settings': django_settings,
        'SITE_BUYER': django_settings.DEFAULT_SITE_ID,
        'SITE_SELLER': django_settings.SELLER_SITE_ID
    }
