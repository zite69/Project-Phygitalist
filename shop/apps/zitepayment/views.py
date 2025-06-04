from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from oscar.core.loading import get_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView
from oscar.apps.checkout.mixins import OrderPlacementMixin
from oscar.apps.partner import strategy
from shop.apps.main.utils.urls import get_absolute_url

from icecream import ic

from shop.apps.zitepayment.models import RazorpayOrder
from .gateway import RazorpayGateway
import logging

logger = logging.getLogger(__package__)

SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')

class RazorPaymentDetailsView(CorePaymentDetailsView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        logger.debug(ctx)
        logger.debug(self.request.basket)
        logger.debug(self.request.strategy)
        basket = self.request.basket
        # logger.debug(dir(ctx))
        # logger.debug(dir(ctx['basket']))
        # line = ctx['basket'].lines.all()[0]
        # logger.debug(dir(line))
        # logger.debug(line)
        # logger.debug(line.product)
        # logger.debug(dir(line.product))
        # logger.debug(line.product.primary_image())
        # logger.debug(dir(line.product.primary_image()))
        logger.debug(basket)
        logger.debug(basket.strategy)
        basket.strategy = strategy.Default()
        basket.save()
        logger.debug(basket.strategy)
        order_number = self.generate_order_number(ctx['basket'])
        gateway = RazorpayGateway()
        receipt = f"order_{order_number}"
        payment_callback = get_absolute_url(settings.DEFAULT_SITE_ID, 'checkout:payment-details')
        order = gateway.create_order(ctx['order_total'].incl_tax, receipt=receipt)
        RazorpayOrder.objects.create(razorpay_order_id=order['id'], basket=basket)
        options = {
            'key': settings.RAZORPAY_KEY,
            'amount': ( ctx['order_total'].incl_tax * 100 ).to_integral_value(),
            'currency': 'INR',
            'name': 'Zite69 Checkout',
            'description': 'Zite69 Checkout',
            'image': 'https://www.zite69.com/static/img/zite69_shop.png',
            'order_id': order['id'],
            'callback_url': payment_callback,
            'prefill': {
                'email': ctx['user'].email,
                'name': ctx['user'].name
            },
            'theme': {
                'color': '#f66569'
            }
        }
        if ctx['user'].phone is not None:
            options['prefill']['phone'] = ctx['user'].phone.as_international

        ctx['options'] = options

        if self.preview:
            #ctx['form'] = RazorpayForm(self.request.POST)
            ctx['order_total_paise'] = ( ctx['order_total'].incl_tax * 100 ).to_integral_value()
        else:
            ctx['amount'] = ( ctx['order_total'].incl_tax * 100 ).to_integral_value()
        return ctx

    def post(self, request, *args, **kwargs):
        logger.debug("Inside payment details post method")
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature', '')
        error = request.POST.get('error', '')
        logger.debug(payment_id, order_id, signature, error)
        logger.debug(request.POST)
        logger.debug(request.basket)
        logger.debug(request.strategy)
        if not payment_id or not order_id:
            return HttpResponseBadRequest(b"Missing payment details from the site")

        gateway = RazorpayGateway()
        if not gateway.verify_payment_signature(payment_id, order_id, signature, error):
            logger.debug("Failed to verify payment signature")
            return self.handle_payment_error(request)

        try:
            razorpay_order = RazorpayOrder.objects.get(razorpay_order_id=order_id)
            logger.debug(razorpay_order)
            basket = razorpay_order.basket
            logger.debug(basket)
            logger.debug(basket == request.basket)
            basket.strategy = request.strategy

            source_type, _ = SourceType.objects.get_or_create(name="Razorpay")
            source = Source(
                source_type=source_type,
                amount_allocated=basket.total_incl_tax,
                amount_debited=basket.total_incl_tax,
                reference=payment_id
                )
            self.add_payment_source(source)
            logger.debug("Added payment source")
            self.add_payment_event("Paid", basket.total_incl_tax, reference=payment_id)
            logger.debug("Added payment event")

            return self.submit(**self.build_submission())
        except Exception as e:
            logger.debug("Got payment exception", e)
            return self.handle_payment_error(f"Failed to finish payment process {str(e)}")

    def handle_payment_error(self, request, error_msg="Payment Failed"):
        return render(request, 'zitepayment/checkout/payment_error.html', {"error": error_msg})

class RazorpayCallbackView(OrderPlacementMixin, TemplateView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.debug(request)
        logger.debug(request.POST)
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        error = request.POST.get('error', '')
        logger.debug(f"Got payment_id: {payment_id} , order_id: {order_id}, signature: {signature}, error: {error}")

        gateway = RazorpayGateway()
        result, message = gateway.verify_payment_signature(payment_id, order_id, signature, error)
        context = self.get_context_data()
        if result:
            context['message'] = "You have successfully placed the order"
            self.template_name = 'oscar/checkout/payment_success.html'
            return self.render_to_response(context)
        else:
            context['message'] = f"Error capturing payment: {message}"
            self.template_name = 'oscar/checkout/payment_error.html'
            return self.render_to_response(context)

