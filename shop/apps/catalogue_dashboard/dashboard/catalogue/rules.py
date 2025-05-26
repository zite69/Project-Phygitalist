import rules

@rules.predicate
def is_superuser(user):
    print(user.is_superuser)
    return user.is_superuser

@rules.predicate
def is_product_owner(user, product):
    return product is None or product == '' or (product is not None and product.seller == user.seller)

@rules.predicate
def is_main_seller_admin(user):
    print(user)
    return user.groups.filter(name='Seller Admin').exists()

@rules.predicate
def is_seller_admin(user, product):
    print(product)
    return product is not None and user.seller_admins.filter(pk__in=[product.seller.pk]).exists()

rules.add_perm('products.can_edit_product', is_superuser | is_main_seller_admin | is_product_owner | is_seller_admin)
rules.add_perm('products.can_qc_product', is_superuser | is_main_seller_admin | is_seller_admin)
