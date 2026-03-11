import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SHIPROCKET_BASE_URL = 'https://apiv2.shiprocket.in/v1/external'
_TOKEN_CACHE_KEY = 'shiprocket_auth_token'
_TOKEN_TTL = 60 * 60 * 9  # 9 hours (tokens last 10 hours)


def _get_token():
    token = cache.get(_TOKEN_CACHE_KEY)
    if token:
        return token
    resp = requests.post(
        f'{SHIPROCKET_BASE_URL}/auth/login',
        json={'email': settings.SHIPROCKET_EMAIL, 'password': settings.SHIPROCKET_PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()['token']
    cache.set(_TOKEN_CACHE_KEY, token, _TOKEN_TTL)
    return token


def _auth_headers():
    return {'Authorization': f'Bearer {_get_token()}'}


def _address_name(address):
    first = (address.first_name or '').strip()
    last = (address.last_name or '').strip()
    return first, last


def create_shiprocket_order(oscar_order):
    """
    Create an order in ShipRocket for the given Oscar order instance.
    Returns the raw JSON response dict.
    Raises requests.HTTPError on API failure.
    """
    billing = oscar_order.billing_address
    shipping = oscar_order.shipping_address
    addr = billing or shipping  # fallback

    b_first, b_last = _address_name(addr) if addr else ('', '')
    s_first, s_last = _address_name(shipping) if shipping else (b_first, b_last)

    def country_name(a):
        return a.country.printable_name if a and a.country else 'India'

    shipping_is_billing = (
        billing is None
        or shipping is None
        or (billing.line1 == shipping.line1 and billing.postcode == shipping.postcode)
    )

    order_items = [
        {
            'name': line.title,
            'sku': line.partner_sku or str(line.id),
            'units': line.quantity,
            'selling_price': str(line.unit_price_incl_tax),
            'discount': '',
            'tax': '',
            'hsn': '',
        }
        for line in oscar_order.lines.all()
    ]

    payload = {
        'order_id': str(oscar_order.number),
        'order_date': oscar_order.date_placed.strftime('%Y-%m-%d %H:%M'),
        'pickup_location': getattr(settings, 'SHIPROCKET_PICKUP_LOCATION', 'Primary'),

        'billing_customer_name': b_first,
        'billing_last_name': b_last,
        'billing_address': addr.line1 if addr else '',
        'billing_address_2': addr.line2 if addr else '',
        'billing_city': addr.line4 if addr else '',
        'billing_pincode': addr.postcode if addr else '',
        'billing_state': addr.state if addr else '',
        'billing_country': country_name(addr),
        'billing_email': oscar_order.email or '',
        'billing_phone': str(addr.phone_number) if addr and addr.phone_number else '',

        'shipping_is_billing': 1 if shipping_is_billing else 0,
        'shipping_customer_name': s_first,
        'shipping_last_name': s_last,
        'shipping_address': shipping.line1 if shipping else '',
        'shipping_address_2': shipping.line2 if shipping else '',
        'shipping_city': shipping.line4 if shipping else '',
        'shipping_pincode': shipping.postcode if shipping else '',
        'shipping_state': shipping.state if shipping else '',
        'shipping_country': country_name(shipping),
        'shipping_email': oscar_order.email or '',
        'shipping_phone': str(shipping.phone_number) if shipping and shipping.phone_number else '',

        'order_items': order_items,
        'payment_method': 'Prepaid',
        'shipping_charges': float(oscar_order.shipping_incl_tax),
        'giftwrap_charges': 0,
        'transaction_charges': 0,
        'total_discount': float(oscar_order.total_discount_incl_tax),
        'sub_total': float(oscar_order.basket_total_incl_tax),

        # Package dimensions — configure in settings if needed
        'length': getattr(settings, 'SHIPROCKET_DEFAULT_LENGTH', 10),
        'breadth': getattr(settings, 'SHIPROCKET_DEFAULT_BREADTH', 10),
        'height': getattr(settings, 'SHIPROCKET_DEFAULT_HEIGHT', 10),
        'weight': getattr(settings, 'SHIPROCKET_DEFAULT_WEIGHT', 0.5),
    }

    resp = requests.post(
        f'{SHIPROCKET_BASE_URL}/orders/create/adhoc',
        json=payload,
        headers=_auth_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
