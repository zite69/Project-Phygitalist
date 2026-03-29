import logging
from collections import defaultdict

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


def create_shiprocket_order(oscar_order, seller=None):
    """
    Create Shiprocket shipments for the given Oscar order.

    If `seller` is provided, only that seller's lines are shipped — intended
    for when a seller initiates shipment themselves from their own order view.

    If `seller` is None (superuser / admin), lines are grouped by seller and
    a separate Shiprocket order is created for each one.

    Shiprocket order IDs take the form "{order_number}-{seller_handle}" to
    keep them unique within Shiprocket while remaining traceable back to the
    Oscar order.

    Financial fields (sub_total, shipping_charges, total_discount) are split
    proportionally across sellers by their share of the basket total.

    Returns:
        dict: {seller_handle: shiprocket_response_dict} for every shipment
              successfully submitted. Raises requests.HTTPError on the first
              API failure.

    Lines whose partner has no linked Seller are skipped with a warning.
    """
    billing = oscar_order.billing_address
    shipping = oscar_order.shipping_address
    addr = billing or shipping

    b_first, b_last = _address_name(addr) if addr else ('', '')
    s_first, s_last = _address_name(shipping) if shipping else (b_first, b_last)

    def country_name(a):
        return a.country.printable_name if a and a.country else 'India'

    shipping_is_billing = (
        billing is None
        or shipping is None
        or (billing.line1 == shipping.line1 and billing.postcode == shipping.postcode)
    )

    # --- group lines by seller -------------------------------------------
    lines_by_seller = defaultdict(list)
    for line in oscar_order.lines.select_related('partner').all():
        line_seller = line.partner.sellers.first() if line.partner else None
        if line_seller is None:
            logger.warning(
                "Order %s line %s (sku=%s) has no resolvable seller — skipping",
                oscar_order.number, line.id, line.partner_sku,
            )
            continue
        # When a specific seller is given, only collect their lines
        if seller is not None and line_seller.pk != seller.pk:
            continue
        lines_by_seller[line_seller].append(line)

    if not lines_by_seller:
        logger.error("Order %s has no lines with resolvable sellers — no shipments created", oscar_order.number)
        return {}

    # Pre-compute order-level totals for proportional splitting
    order_total = float(oscar_order.basket_total_incl_tax) or 1  # avoid div/0
    total_shipping = float(oscar_order.shipping_incl_tax)
    total_discount = float(oscar_order.total_discount_incl_tax)

    results = {}

    for seller, lines in lines_by_seller.items():
        # Resolve pickup location — fall back to settings if not registered
        pickup_location = getattr(settings, 'SHIPROCKET_PICKUP_LOCATION', 'work')
        try:
            seller.pickup_addresses.get()
            pickup_location = seller.handle
        except seller.pickup_addresses.model.DoesNotExist:
            logger.warning(
                "Seller %s has no pickup address for order %s — falling back to settings",
                seller.handle, oscar_order.number,
            )

        order_items = [
            {
                'name': line.title,
                'sku': line.partner_sku or str(line.id),
                'units': line.quantity,
                'selling_price': float(line.unit_price_incl_tax),
                'discount': 0,
                'tax': 0,
                'hsn': '',
            }
            for line in lines
        ]

        sub_total = sum(float(line.unit_price_incl_tax) * line.quantity for line in lines)
        share = sub_total / order_total
        order_id = f"{oscar_order.number}-{seller.handle}"

        payload = {
            'order_id': order_id,
            'order_date': oscar_order.date_placed.strftime('%Y-%m-%d %H:%M'),
            'pickup_location': pickup_location,

            'billing_customer_name': b_first,
            'billing_last_name': b_last,
            'billing_address': addr.line1 if addr else '',
            'billing_address_2': addr.line2 if addr else '',
            'billing_city': addr.line4 if addr else '',
            'billing_pincode': addr.postcode if addr else '',
            'billing_state': addr.state if addr else '',
            'billing_country': country_name(addr),
            'billing_email': oscar_order.email or '',
            'billing_phone': addr.phone_number.as_national.replace(' ', '').lstrip('0'),

            'shipping_is_billing': shipping_is_billing,
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
            'shipping_charges': round(total_shipping * share, 2),
            'giftwrap_charges': 0,
            'transaction_charges': 0,
            'total_discount': round(total_discount * share, 2),
            'sub_total': round(sub_total, 2),

            'length': getattr(settings, 'SHIPROCKET_DEFAULT_LENGTH', 10),
            'breadth': getattr(settings, 'SHIPROCKET_DEFAULT_BREADTH', 10),
            'height': getattr(settings, 'SHIPROCKET_DEFAULT_HEIGHT', 10),
            'weight': getattr(settings, 'SHIPROCKET_DEFAULT_WEIGHT', 0.5),
        }

        logger.debug("Creating Shiprocket order %s for seller %s", order_id, seller.handle)

        resp = requests.post(
            f'{SHIPROCKET_BASE_URL}/orders/create/adhoc',
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )

        logger.debug("Shiprocket response for %s: %s", order_id, resp.text)
        resp.raise_for_status()
        results[seller.handle] = resp.json()

    return results


def create_pickup_location(seller):
    """
    Register a seller's pickup address with Shiprocket.

    Uses seller.handle as the pickup_location name (the unique label
    Shiprocket uses to identify this address on future orders).

    Returns the raw JSON response dict.
    Raises ValueError if the seller has no pickup address.
    Raises requests.HTTPError on API failure.
    """
    try:
        pickup = seller.pickup_addresses.get()
    except seller.pickup_addresses.model.DoesNotExist:
        raise ValueError(
            f"Seller '{seller.handle}' has no pickup address — "
            "cannot register with Shiprocket."
        )

    user = seller.user
    if user.phone:
        phone = user.phone.as_national.replace(' ', '').lstrip('0')
    else:
        phone = ''

    payload = {
        'pickup_location': seller.handle,
        'name': seller.name,
        'email': user.email or '',
        'phone': phone,
        'address': pickup.line1 or '',
        'address_2': pickup.line2 or '',
        'city': pickup.line4 or '',
        'state': pickup.state or '',
        'country': pickup.country.printable_name if pickup.country else 'India',
        'pin_code': pickup.postcode or '',
    }

    logger.debug("Creating Shiprocket pickup location for seller %s: %s", seller.handle, payload)

    resp = requests.post(
        f'{SHIPROCKET_BASE_URL}/settings/company/addpickup',
        json=payload,
        headers=_auth_headers(),
        timeout=30,
    )

    logger.debug("Shiprocket pickup location response: %s", resp.text)
    resp.raise_for_status()
    return resp.json()
