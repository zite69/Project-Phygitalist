from django import template
from django.template.defaulttags import URLNode
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.html import conditional_escape
from django.template.base import TemplateSyntaxError, kwarg_re

class SiteURLNode(URLNode):
    def __init__(self, site_id, view_name, args, kwargs, asvar):
        super().__init__(view_name, args, kwargs, asvar)
        if site_id == '':
            self.site_id = settings.DEFAULT_SITE_ID
        else:
            self.site_id = site_id

    def __repr__(self):
        return "<%s view_name='%s' args=%s kwargs=%s as=%s>" % (
            self.__class__.__qualname__,
            self.view_name,
            repr(self.args),
            repr(self.kwargs),
            repr(self.asvar),
        )

    def render(self, context):
        from django.urls import NoReverseMatch, reverse

        args = [arg.resolve(context) for arg in self.args]
        kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        view_name = self.view_name.resolve(context)
        site_id = self.site_id.resolve(context)
        if site_id == '':
            site_id = settings.DEFAULT_SITE_ID
        urlconf = 'shop.urls' if site_id == settings.DEFAULT_SITE_ID else 'shop.urls_seller'
        site = Site.objects.get(id=site_id)
        try:
            current_app = context.request.current_app
        except AttributeError:
            try:
                current_app = context.request.resolver_match.namespace
            except AttributeError:
                current_app = None
        # Try to look up the URL. If it fails, raise NoReverseMatch unless the
        # {% url ... as var %} construct is used, in which case return nothing.
        url = ""
        try:
            url = reverse(view_name, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
        except NoReverseMatch:
            if self.asvar is None:
                raise

        http = 'https' if settings.USE_HTTPS else 'http'
        url = f"{http}://{site.domain}{url}"

        if self.asvar:
            context[self.asvar] = url
            return ""
        else:
            if context.autoescape:
                url = conditional_escape(url)
            return url

register = template.Library()

@register.tag
def site_url(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(
            "'%s' takes at least two arguments, SITE_ID and a URL pattern name." % bits[0]
        )
    site_id = parser.compile_filter(bits[1])
    viewname = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None
    bits = bits[3:]
    if len(bits) >= 3 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]

    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to url tag")
        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)
        else:
            args.append(parser.compile_filter(value))

    return SiteURLNode(site_id, viewname, args, kwargs, asvar)


