from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext as _
from shop.apps.cmsplugins.models import FeaturedProduct, FeaturedProductCollection
from . import forms

@plugin_pool.register_plugin
class FeaturedProductCollectionPlugin(CMSPluginBase):
    model = FeaturedProductCollection
    module = _("Zite69")
    name = _("Featured Product Collection")
    render_template = "cmsplugins/featured_collection.html"
    allow_children = True
    child_classes = ["FeaturedProductPlugin"]

    def render(self, context, instance, placeholder):
        context.update({"instance": instance})
        return context

@plugin_pool.register_plugin
class FeaturedProductPlugin(CMSPluginBase):
    model = FeaturedProduct
    # form = forms.FeaturedProductForm
    autocomplete_fields = ["product"]
    module = _("Zite69")
    name = _("Featured Product")
    render_template = "cmsplugins/featured_product.html"
    allow_children = True
    parent_classes = ["FeaturedProductCollectionPlugin"]

    def render(self, context, instance, placeholder):
        context.update({"instance": instance})
        return context
