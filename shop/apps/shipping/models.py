from django.db import models

from oscar.apps.shipping.models import *  # noqa


class ShipRocketOrder(models.Model):
    """Stores ShipRocket shipment details linked to an Oscar order number."""

    order_number = models.CharField(max_length=128, unique=True, db_index=True)
    shiprocket_order_id = models.CharField(max_length=64, blank=True)
    shipment_id = models.CharField(max_length=64, blank=True)
    awb_code = models.CharField(max_length=64, blank=True)
    courier_name = models.CharField(max_length=128, blank=True)
    label_url = models.URLField(blank=True)
    status = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'shipping'
        ordering = ['-created_at']

    def __str__(self):
        return f'ShipRocket order for Oscar #{self.order_number} (SR: {self.shiprocket_order_id})'
