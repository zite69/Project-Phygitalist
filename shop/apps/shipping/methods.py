from oscar.apps.shipping.methods import Base
from oscar.core import prices
from decimal import Decimal as D

class ShipRocketMethod(Base):
    code = 'shiprocket'
    name = 'Shiprocket Shipping'
    description = 'Shiprocket Shipping Method'

    def calculate(self, basket):
        return prices.Price(
            currency=basket.currency,
            excl_tax=D("0.00"),
            tax=D("0.00"),
        )

