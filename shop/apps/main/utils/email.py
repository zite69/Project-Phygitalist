from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, engines
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.contrib.staticfiles import finders
from functools import lru_cache
#from .urls import get_site_base_uri
import logging

def reset_template_cache():
    for engine in engines.all():
        engine.engine.template_loaders[0].reset()

logger = logging.getLogger('shop.apps.main.utils')

@lru_cache()
def logo_data():
    with open(finders.find('img/zite69_shop.png'), 'rb') as f:
        logo_data = f.read()
    logo = MIMEImage(logo_data)
    logo.add_header('Content-ID', '<logo>')
    return logo

@lru_cache()
def image_data(imgpath, imgcid):
    with open(finders.find(imgpath), 'rb') as f:
        image_data = f.read()
    image = MIMEImage(image_data)
    image.add_header('Content-ID', imgcid)
    return image

def send_waitlist_welcome(email):
    logger.debug(f"Called to send waitlist email to {email}")
    context = {
        "base_uri": "https://www.zite69.com"
    }
    html_content = render_to_string("email/waitlist.html", context=context)
    text_content = strip_tags(html_content)

    message = EmailMultiAlternatives(
            subject="You have joined our waitlist!",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
    )

    message.mixed_subtype = 'related'
    message.attach_alternative(html_content, "text/html")
    # message.attach(logo_data())

    #returns the number of messages sent. in this case should be either 1 or 0
    return message.send(fail_silently=False)

def send_email(email, **kwargs):
    # template = kwargs.get("template", "email/otp.html")
    # logo = kwargs.get("logo", False)
    # from_email = kwargs.get("from_email", settings.DEFAULT_FROM_EMAIL)
    # subject = kwargs.get("subject", "Your OTP to login to our site")
    # images = kwargs.get("images", {})
    # cc = kwargs.get("cc", [])
    # bcc = kwargs.get("bcc", [])
    # base_uri = kwargs.get("base_uri", get_site_base_uri())
    # kwargs['base_uri'] = base_uri
    kwargs = kwargs | ({
        "template": "email/otp.html",
        "logo": False,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "subject": "Your OTP to login to our site",
        "images": {},
        "cc": [],
        "bcc": [],
        "base_uri": "https://www.zite69.com",
        "whatsapp_link": f"https://wa.me/{settings.WHATSAPP_NUMBER}",
        "SITE_BUYER": settings.DEFAULT_SITE_ID,
        "SITE_SELLER": settings.SELLER_SITE_ID
        } | kwargs)
    template = kwargs.get("template")
    logo = kwargs.get("logo")
    from_email = kwargs.get("from_email")
    subject = kwargs.get("subject")
    images = kwargs.get("images")
    cc = kwargs.get("cc")
    bcc = kwargs.get("bcc")
 
    html_content = render_to_string(template, context=kwargs)
    # return html_content
    text_content = strip_tags(html_content)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[email]
    )
    if cc:
        message.cc = cc
    if bcc:
        message.bcc = bcc

    message.mixed_subtype = 'related'
    message.attach_alternative(html_content, "text/html")
    if logo:
        message.attach(logo_data())
    if images:
        for k in images:
            message.attach(image_data(k, images[k]))

    return message.send(fail_silently=False)

def send_email_otp(email, otp, **kwargs):
    return send_email(email, otp=otp, template="email/otp.html", subject="Your OTP to login to our site", **kwargs)

def send_email_verification(email, otp, **kwargs):
    return send_email(email, otp=otp, template="email/verification.html", subject="Verify your email address", **kwargs)

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

def send_email_seller_welcome(user, **kwargs):
    kwargs = kwargs | ({
        "template": "email/welcome_paidseller.html",
        "subject": "Welcome to zite69",
        } | kwargs)
    kwargs['user'] = user

    return send_email(user.email, **kwargs)

def send_seller_approval(user, registration, **kwargs):
    kwargs = kwargs | ({
        "template": "email/approval_registration.html",
        "subject": "Your Seller Registration has been approved!"
        } | kwargs)
    kwargs['user'] = user
    kwargs['registration'] = registration

    return send_email(user.email, **kwargs)

def send_seller_rejection(user, registration, **kwargs):
    kwargs = kwargs | ({
        "template": "email/onboarding_rejection_pending.html",
        "subject": "Your Seller Registration has been rejected"
        } | kwargs)

    kwargs['user'] = user
    kwargs['registration'] = registration

    return send_email(user.email, **kwargs)

def send_onboarding_approval(user, seller, **kwargs):
    kwargs = kwargs | ({
        "template": "email/mjml/add_product.html",
        "subject": "Your Seller Onboarding has been approved"
        } | kwargs)

    kwargs['user'] = user
    kwargs['seller'] = seller

    return send_email(user.email, **kwargs)

def send_onboarding_rejection(user, seller, **kwargs):
    kwargs = kwargs | ({
        "template": "email/pending_rejection.html",
        "subject": "There were some issues with your Seller onboarding"
        } | kwargs)

    kwargs['user'] = user
    kwargs['seller'] = seller

    return send_email(user.email, **kwargs)

def send_products_approved(seller, products, **kwargs):
    kwargs = kwargs | ({
        "template": "email/product_approval.html",
        "subject": "Your product(s) is/are approved!"
        })
    if type(products) != list:
        products = [products]

    kwargs['products'] = products
    kwargs['seller'] = seller
    kwargs['user'] = seller.user

    return send_email(seller.user.email, **kwargs)
