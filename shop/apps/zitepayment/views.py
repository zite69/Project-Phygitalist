from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from oscar.core.loading import get_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView

from .gateway import RazorpayGateway

SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')

class RazorPaymentDetailsView(CorePaymentDetailsView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        print("inside get_context_data")
        print(ctx)
        print(dir(ctx))
        order_number = self.generate_order_number(ctx['basket'])
        gateway = RazorpayGateway()
        receipt = f"order_{order_number}"
        order = gateway.create_order(ctx['order_total'].incl_tax, receipt=receipt)
        options = {
            'key': settings.RAZORPAY_KEY,
            'amount': ( ctx['order_total'].incl_tax * 100 ).to_integral_value(),
            'currency': 'INR',
            'name': 'Zite69 Basket',
            'description': 'Zite69 Checkout',
            'image': 'https://www.zite69.com/static/img/zite69_shop.png',
            'order_id': order['id'],
            'customer_name': ctx['user'].name,
            'customer_email': ctx['user'].email,
            'customer_phone': ctx['user'].phone,
            'callback_url': 'https://beta.zite69.com/en/checkout/callback/'
        }
        ctx['options'] = options

        if self.preview:
            #ctx['form'] = RazorpayForm(self.request.POST)
            ctx['order_total_paise'] = ( ctx['order_total'].incl_tax * 100 ).to_integral_value()
        else:
            ctx['amount'] = ( ctx['order_total'].incl_tax * 100 ).to_integral_value()
        return ctx

class RazorpayCallbackView(TemplateView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print(request)
        print(request.POST)
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        error = request.POST.get('error', '')
        print(f"Got payment_id: {payment_id} , order_id: {order_id}, signature: {signature}, error: {error}")

        gateway = RazorpayGateway()
        result, message = gateway.verify_payment_signature(payment_id, order_id, signature, '95', error)
        context = self.get_context_data()
        if result:
            context['message'] = "You have successfully placed the order"
            self.template_name = 'oscar/checkout/payment_success.html'
            return self.render_to_response(context)
        else:
            context['message'] = f"Error capturing payment: {message}"
            self.template_name = 'oscar/checkout/payment_error.html'
            return self.render_to_response(context)

