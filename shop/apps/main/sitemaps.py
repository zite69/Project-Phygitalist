from django.contrib import sitemaps
from django.urls import reverse
from cms.sitemaps import CMSSitemap

class StaticPagesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return ["careers"]

    def location(self, item):
        return reverse(item)


SITEMAPS = {
    "static": StaticPagesSitemap,
    "cmspages": CMSSitemap
}
