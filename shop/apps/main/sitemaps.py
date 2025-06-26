from django.contrib import sitemaps
from django.urls import reverse
from cms.sitemaps import CMSSitemap
from shop.apps.catalogue.models import Category, Product

class StaticPagesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return ["careers"]

    def location(self, item):
        return reverse(item)

class CategorySitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return Category.objects.all()

    def location(self, item):
        return reverse('catalogue:category', kwargs={"category_slug": item.slug, 'pk': item.id})

class ProductSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return Product.objects.browsable()

    def location(self, item):
        return reverse('catalogue:detail', kwargs={"product_slug": item.slug, "pk": item.id})


SITEMAPS = {
    "static": StaticPagesSitemap,
    "cmspages": CMSSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap
}
