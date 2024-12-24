from oscar.apps.address.abstract_models import AbstractCountry
from .abstract_models import AbstractOrganizationAddress, AbstractUserAddress
from oscar.core.loading import is_model_registered

if not is_model_registered('address', 'UserAddress'):
    class UserAddress(AbstractUserAddress):
        pass

if not is_model_registered('address', 'OrganizationAddress'):
    class OrganizationAddress(AbstractOrganizationAddress):
        pass


if not is_model_registered('address', 'Country'):
    class Country(AbstractCountry):
        pass
