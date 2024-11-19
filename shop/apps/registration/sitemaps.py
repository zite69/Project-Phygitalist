from django.contrib import sitemaps
from django.urls import reverse_lazy
from cms.sitemaps import CMSSitemap

class StaticPagesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return ["registration:home"]

    def location(self, item):
        return reverse_lazy(item)

SITEMAPS = {
    "static": StaticPagesSitemap,
    "cmspages": CMSSitemap
}
