from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, engines
from django.utils.html import strip_tags

def reset_template_cache():
    for engine in engines.all():
        engine.engine.template_loaders[0].reset()

from email.mime.image import MIMEImage

from django.contrib.staticfiles import finders
from functools import lru_cache
import logging

logger = logging.getLogger('shop.apps.main.utils')

@lru_cache()
def logo_data():
    with open(finders.find('img/zite69_shop.png'), 'rb') as f:
        logo_data = f.read()
    logo = MIMEImage(logo_data)
    logo.add_header('Content-ID', '<logo>')
    return logo

def send_waitlist_welcome(email):
    logger.debug(f"Called to send waitlist email to {email}")
    html_content = render_to_string("email/waitlist.html")
    text_content = strip_tags(html_content)

    message = EmailMultiAlternatives(
            subject="You have joined our waitlist!",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
    )

    message.mixed_subtype = 'related'
    message.attach_alternative(html_content, "text/html")
    message.attach(logo_data())

    #returns the number of messages sent. in this case should be either 1 or 0
    return message.send(fail_silently=False)

def send_email(email, **kwargs):
    template = kwargs.get("template", "email/otp.html")
    logo = kwargs.get("logo", True)
    from_email = kwargs.get("from_email", settings.DEFAULT_FROM_EMAIL)
    subject = kwargs.get("subject", "Your OTP to login to our site")

    html_content = render_to_string(template, context=kwargs)
    text_content = strip_tags(html_content)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )

    message.mixed_subtype = 'related'
    message.attach_alternative(html_content, "text/html")
    if logo:
        message.attach(logo_data())

    return message.send(fail_silently=False)

def send_email_otp(email, otp):
    return send_email(email, otp=otp, template="email/otp.html", subject="Your OTP to login to our site")

def send_email_invite(email, ctx):
    #Default context values
    def_ctx = {
        'template': 'email/invitation.html',
        'subject': 'You have been invited to join our site',
        'expiry': '7 days'
    }

    #Set defaults for context if they don't exist'
    for k in def_ctx:
        ctx.setdefault(k, def_ctx[k])

    return send_email(email, **ctx)
