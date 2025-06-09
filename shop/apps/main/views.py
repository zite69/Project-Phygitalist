from django.db.models.functions import Sign
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .utils.email import send_email_otp
import logging
from allauth.account.views import LoginView as OGLoginView
from allauth.account.forms import RequestLoginCodeForm
from allauth.utils import get_form_class
from allauth.account import app_settings
from shop.apps.user.forms import Zite69SignupForm
from shop.apps.otp.forms import EmailPhoneOtpRequestForm, OtpVerificationForm
from shop.apps.catalogue.models import Product
from shop.apps.main.forms import BuyQuickForm

logger = logging.getLogger("shop.apps.main")

# Create your views here.

class LoginView(OGLoginView):
    
    def dispatch(self, request, *args, **kwargs):
        next_url = self.get_next_url()
        logger.debug("login dispatch: next_url: ")
        logger.debug(next_url)
        if next_url != '' and next_url is not None:
            request.session['next'] = next_url
            request.session.save()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['request_code_form'] = EmailPhoneOtpRequestForm()
        ctx['signup_form'] = Zite69SignupForm()
        ctx['verify_code_form'] = OtpVerificationForm()

        return ctx

class BuyQuickView(FormView):
    form_class = BuyQuickForm
    template_name = "oscar/catalogue/buyquick.html"
    success_url = reverse_lazy("checkout:index")

    def form_valid(self, form):
        product_id = form.cleaned_data.get('product_id')
        logger.debug("product_id")
        logger.debug(product_id)
        product = Product.objects.get(id=product_id)
        logger.debug(product)
        logger.debug(self.request.basket)
        self.request.basket.add_product(product, 1)
        logger.debug(self.success_url)
        return HttpResponseRedirect(self.success_url)

def home(request):
    context = {}

    return render(request, 'main/index.html', context)

def test(request):
    resp = send_email_otp('arunkakorp@gmail.com', otp='123412', cc=['arun@kumars.io'])
    logger.debug("Got response from send_email_otp:")
    logger.debug(resp)

    return render(request, 'main/index.html')

def fivehundred(request):
    num = 1/0
    return render(request, 'error/500.html')

def not_found(request, exception):
    return render(request, "error/404.html", {}, status=404)

def server_error(request, exception=None):
    return render(request, "error/500.html", {}, status=500)

def unauthorized(request, exception=None):
    return render(request, "error/403.html", {}, status=403)
