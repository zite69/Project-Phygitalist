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
from django.urls import include, path, resolve
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView
from shop.apps.main.views import home
from debug_toolbar.toolbar import debug_toolbar_urls
from django.http import Http404, HttpResponseRedirect
from django.conf.urls import (handler404, handler500)

handler404 = 'shop.apps.main.views.not_found'
handler500 = 'shop.apps.main.views.server_errror'

urlpatterns = i18n_patterns(
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', admin.site.urls),
    path('filer/', include('filer.urls')),
    path('accounts/', include('allauth.urls')),
    path('messages/', include('django_messages.urls')),
    path('careers/', TemplateView.as_view(template_name='main/career.html')),
    path('mentor/', TemplateView.as_view(template_name='main/mentor.html')),
    path('sellerschool/', TemplateView.as_view(template_name='main/sellerschool.html')),
    #path('', home, name='home'),
    path('otp/', include((apps.get_app_config('otp').urls[0], 'otp'), namespace='otp')),
    path('membership/', include((apps.get_app_config('membership').urls[0], 'membership'), namespace='membership')),
    #path('referrals/', include('pinax.referrals.urls', namespace='pinax_referrals')),
    path('', include(apps.get_app_config('main').urls[0])),
    path('', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = debug_toolbar_urls() + urlpatterns
