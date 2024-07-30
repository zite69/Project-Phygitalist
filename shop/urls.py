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
from shop.apps.main.views import home
from debug_toolbar.toolbar import debug_toolbar_urls
from django.http import Http404, HttpResponseRedirect


class OscarCMSResolver(object):
    def resolve(self, request):
        path = request.path
        oscar_urls = apps.get_app_config('main').urls[0]
        for url_pattern in oscar_urls:
            try:
                resolver_match = resolve(path)
                if resolver_match.url_name is not None and resolver_match.url_name in url_pattern.name:
                    args = [arg for arg in resolver_match.args if arg is not None]
                    kwargs = {key: value for key, value in resolver_match.kwargs.items() if value is not None}
                    return resolver_match.func(request, *args, **kwargs)
            except Http404:
                pass
        cms_resolver_match = resolve(path, urlconf='cms.urls')
        args = [arg for arg in cms_resolver_match.args if arg is not None]
        kwargs = {key: value for key, value in cms_resolver_match.kwargs.items() if value is not None}
        return cms_resolver_match.func(request, *args, **kwargs)
        #return resolve(path, urlconf='cms.urls').func(request)

def oscar_cms_resolver(request):
    return OscarCMSResolver().resolve(request)

urlpatterns = i18n_patterns(
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', admin.site.urls),
    path('filer/', include('filer.urls')),
    #path('', home, name='home'),
    path('shop/', include(apps.get_app_config('main').urls[0])),
    path('', include('cms.urls')),
    #path('', oscar_cms_resolver),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += debug_toolbar_urls()

