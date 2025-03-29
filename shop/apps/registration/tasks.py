from shop.apps.main.utils.bank import get_ifsc_details
from shop.apps.zitepayment.models import BankAccount, SWIFT_REX
from shop.apps.address.models import OrganizationAddress
from shop.apps.address.utils import get_default_country
from django.contrib.auth import get_user_model
from celery import shared_task

india = None

def parse_address(address):
    *parsed_address, city, state, pincode = map(lambda e: e.strip(), address.split(","))
    # Some basic validation to ensure we have got a pincode after the last comma
    try:
        int(pincode)
    except ValueError:
        pincode = ""

    return ",".join(parsed_address), city, state, pincode

@shared_task()
def update_bank_details(ifsc_code, bankaccount_id):
    global india 
    if india is None:
        india  = get_default_country()
    bank_details = get_ifsc_details(ifsc_code)
    address, city, state, pincode = parse_address(bank_details['ADDRESS'])
    bank_address = OrganizationAddress.objects.create(
        organization_name = bank_details['BANK'] + ' ' + bank_details['BRANCH'],
        line1 = address,
        line4 = city,
        state = state,
        postcode = pincode,
        country = india
    )
    if SWIFT_REX.match(bank_details['SWIFT']):
        swift = bank_details['SWIFT']
    else:
        swift = None

    account = BankAccount.objects.get(id=bankaccount_id)
    account.branch_address = bank_address
    account.imps = bank_details['IMPS']
    account.rtgs = bank_details['RTGS']
    account.neft = bank_details['NEFT']
    account.micr = bank_details['MICR']
    account.swift = swift
    account.contact = bank_details['CONTACT']
    account.save()
