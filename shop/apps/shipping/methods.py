from oscar.apps.shipping.methods import Base
from decimal import Decimal as D

class ShipRocketMethod(Base):
    code = 'shiprocket'
    name = 'Shiprocket Shipping'
    description = 'Shiprocket Shipping Method'

    def calculate_charge_excl_tax(self, basket):
        return D("0.0")

