import rules

@rules.predicate
def is_superuser(user):
    return user.is_superuser

@rules.predicate
def is_product_owner(user, product):
    return product.seller == user.seller

@rules.predicate
def is_main_seller_admin(user):
    return user.groups.filter(name='Seller Admin').exists()

@rules.predicate
def is_seller_admin(user, product):
    return user.seller_admins.filter(pk__in=[product.seller.pk]).exists()

rules.add_perm('products.can_edit_product', is_superuser | is_main_seller_admin | is_product_owner | is_seller_admin)
