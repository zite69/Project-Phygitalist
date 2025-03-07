import razorpay
from django.conf import settings
from oscar.apps.payment.exceptions import PaymentError
from django.urls import reverse

from icecream import ic

client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

class RazorpayGateway:
    def __init__(self):
        self.client = client

    def create_order(self, amount, receipt=None):
        amount = int(amount * 100)
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": '1'
            }
        try:
            # order = self.client.order.create(data=data)
            order = self.client.order.create(data)
            return order
        except Exception as e:
            raise PaymentError(f"Error creating Razorpay order: {str(e)}")

    def verify_payment_signature(self, payment_id, order_id, signature, error):
        try:
            result = self.client.utility.verify_payment_signature({
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
                })
        except Exception as e:
            ic(f"verify_payment_signature failed: {str(e)}")
            return False, 'Invalid signature'

        if result is not None:
            try:
                res = self.verify_payment(payment_id, order_id)
                if res:
                    return True, 'success'
                else:
                    return False, 'Failed to verify payment'
            except Exception as e:
                return False, f"Failed to capture payment {str(e)}"
        else:
            return False, f"Error verifying signature: {error}"

    def verify_payment(self, payment_id, order_id):
        """
        Verify payment with Razorpay
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            print("in verify_payment")
            # ic(payment_authorized)
            # ic(type(payment_authorized['amount']))
            # payment = self.client.payment.capture(payment_id, {
            #     'amount': int(payment_authorized['amount']),
            #     'currency': 'INR'
            # })
            ic(payment)
            if payment['order_id'] == order_id and payment['status'] == 'captured':
                print("returning True")
                return True
            print("returning False")
            return False
        except Exception as e:
            raise PaymentError(f"Error verifying Razorpay payment: {str(e)}")

