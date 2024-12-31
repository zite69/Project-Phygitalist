from shop.apps.seller.models import Seller
import rules

@rules.predicate
def is_seller_account(user, seller):
    return seller.user == user

@rules.predicate
def is_superuser(user):
    return user.is_superuser

@rules.predicate
def is_selleradmin(user):
    return user.groups.filter(name='Seller Admin').exists()

rules.add_perm('seller.view_media', is_seller_account | is_selleradmin)
