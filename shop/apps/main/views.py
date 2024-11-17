from django.shortcuts import render
from .utils.email import send_email_otp
import logging

logger = logging.getLogger("shop.apps.main")

# Create your views here.

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
