import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.orders import views as core_views

from shop.apps.shipping.api import create_shiprocket_order
from shop.apps.shipping.models import ShipRocketOrder

logger = logging.getLogger(__name__)


class OrderDetailView(core_views.OrderDetailView):
    order_actions = core_views.OrderDetailView.order_actions + ('ship_order',)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx['shiprocket_order'] = ShipRocketOrder.objects.get(
                order_number=self.object.number
            )
        except ShipRocketOrder.DoesNotExist:
            ctx['shiprocket_order'] = None
        return ctx

    def ship_order(self, request, order):
        if ShipRocketOrder.objects.filter(order_number=order.number).exists():
            messages.warning(request, _("This order has already been submitted to ShipRocket."))
            return self.reload_page()

        try:
            data = create_shiprocket_order(order)
        except Exception as e:
            logger.exception("ShipRocket API error for order %s", order.number)
            messages.error(request, _("ShipRocket error: %s") % str(e))
            return self.reload_page()

        ShipRocketOrder.objects.create(
            order_number=order.number,
            shiprocket_order_id=str(data.get('order_id', '')),
            shipment_id=str(data.get('shipment_id', '')),
            awb_code=data.get('awb_code', ''),
            courier_name=data.get('courier_name', ''),
            label_url=data.get('label_url', ''),
            status=data.get('status', ''),
            raw_response=data,
        )
        messages.success(request, _("Order successfully submitted to ShipRocket."))
        return self.reload_page()
