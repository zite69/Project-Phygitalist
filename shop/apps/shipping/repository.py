from oscar.apps.shipping.repository import Repository as CoreRepository
from shop.apps.shipping.methods import ShipRocketMethod

class Repository(CoreRepository):
    def get_available_shipping_methods(self, basket, user=None, shipping_addr=None, request=None):
        # Return a list of available shipping method instances
        return [ShipRocketMethod()]
