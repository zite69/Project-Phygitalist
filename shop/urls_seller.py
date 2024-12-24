"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.apps import apps
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView
from debug_toolbar.toolbar import debug_toolbar_urls
from django.http import Http404, HttpResponseRedirect
from django.conf.urls import (handler404, handler500)
from django.contrib.sitemaps.views import sitemap
from shop.apps.registration.sitemaps import SITEMAPS
from shop.apps.registration.views import MultiFormView
from shop.apps.registration.forms import PickupAddressForm, BankDetailsForm, SellerPickupAddressForm, SellerRemainingForm
from shop.apps.seller.models import Seller
import logging
from django_downloadview import ObjectDownloadView

logger = logging.getLogger("shop.urls_seller")
# logger.debug(f"urls: {apps.get_app_config('registration').urls[0]}")

handler404 = 'shop.apps.main.views.not_found'
handler500 = 'shop.apps.main.views.server_error'


ONBOARDING_FORM_CLASSES = {
    "pickup": SellerPickupAddressForm,
    "bank": BankDetailsForm,
    "seller": SellerRemainingForm
}

#urlpatterns = i18n_patterns()
urlpatterns = i18n_patterns(
    path('sitemap.xml', sitemap, { "sitemaps": SITEMAPS }, name="seller.sitemap"),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('dashboard/onboarding/', MultiFormView.as_view(form_classes=ONBOARDING_FORM_CLASSES), name="onboarding-wizard"),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('messages/', include('django_messages.urls')),
    path('mentor/', TemplateView.as_view(template_name='main/mentor.html'), name="mentor"),
    path('sellerschool/', TemplateView.as_view(template_name='main/sellerschool.html'), name="sellerschool"),
    # path('dashboard/onboarding/', TemplateView.as_view(template_name='oscar/dashboard/wizard.html'), name="onboarding-wizard"), #Just a temporary URL for Edwin to work on the template
    path('invitation/', include((apps.get_app_config('invitation').urls[0], 'invitation'), namespace='invitation')),
    path('otp/', include((apps.get_app_config('otp').urls[0], 'otp'), namespace='otp')),
    path('registration/', include((apps.get_app_config('registration').urls[0], 'registration'), namespace='registration')),
    re_path('/protected/seller/(?P<pk>)/gstin/(?P<filename>)', ObjectDownloadView.as_view(model=Seller, file_field="gstin_file"), name="gtstin-file-protected-view"),
    re_path('/protected/seller/(?P<pk>)/pan/(?P<filename>)', ObjectDownloadView.as_view(model=Seller, file_field="pan_file"), name="pan-file-protected-view"),
    re_path('/protected/seller/(?P<pk>)/signature/(?P<filename>)', ObjectDownloadView.as_view(model=Seller, file_field='signature_file')),
    #path('', include(apps.get_app_config('main').urls[0])),
    path('dashboard/', apps.get_app_config('dashboard').urls),
    path('catalog/', apps.get_app_config('catalogue').urls),
    path('customer/', apps.get_app_config('customer').urls),
    path('', include('djangocms_forms.urls')),
    path('', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.PROTECTED_URL, document_root=settings.PROTECTED_ROOT)
    urlpatterns = debug_toolbar_urls() + urlpatterns
