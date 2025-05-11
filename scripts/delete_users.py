from shop.apps.zitepayment.models import BankAccount
from shop.apps.registration.models import SellerRegistration, SellerProduct
from shop.apps.seller.models import Seller
from shop.apps.user.models import User

def is_num(arg):
    try:
        int(arg)
        return True
    except ValueError:
        return False

def delete_user_records(user):
    BankAccount.objects.filter(user=user).delete()
    SellerProduct.objects.filter(seller_reg__user=user).delete()
    SellerRegistration.objects.filter(user=user).delete()
    Seller.objects.filter(user=user).delete()
    user.delete()

def run(*args):
    if len(args) == 0:
        print("Please specify username, email or phonenumber to delete")

    for arg in args:
        print("Deleting user with: ", arg)
        if '@' in arg:
            print("Deleting user with email address: ", arg)
            try:
                user = User.objects.get(email=arg)
                print(user)
            except User.DoesNotExist:
                print("Unable to find user with email: ", arg)
                continue

            delete_user_records(user) 
            print("Deleted user")
        elif is_num(arg):
            try:
                user = User.objects.get(phone=arg)
                print(user)
            except User.DoesNotExist:
                print("Unable to find user with phone: ", arg)
                continue

            delete_user_records(user)
            print("Deleted user")
        else: #Check if we are deleting by username
            print("Deleting user with username: ", arg)
            try:
                user = User.objects.get(username=arg)
                print(user)
            except User.DoesNotExist:
                print("Unable to find user with phone: ", arg)
                continue

            delete_user_records(user)
            print("Deleted user")
