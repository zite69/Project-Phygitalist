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
