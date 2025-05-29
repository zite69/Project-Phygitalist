from oscar.apps.order.signals import order_placed
from shop.apps.main.utils.email import send_order_placed_to_seller
import logging

logger = logging.getLogger(__package__)

def notify_seller(**kwargs):
    order = kwargs['order']
    sellers = set()
    for line in order.lines.all():
        sellers.add(line.product.seller)

    sellers = list(sellers)
    for seller in sellers:
        resp = send_order_placed_to_seller(seller, order)
        logger.debug(f"Sent email to seller: {seller} for order: {order}. Got response: {resp}")

order_placed.connect(notify_seller)
