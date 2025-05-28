from django.conf import settings
from django.template.loader import get_template
from django.template.base import VariableNode
from shop.apps.main.utils.email import send_email

MAP_TO_SUBJECT = {
    'otp_buyers': 'Your OTP to login to our site',
    'otp_sellers': 'Your OTP to login to our site',
    'item_shipped': 'Item shipped to you',
    'invitation':  'Your Invitation link',
    'approval_registration': 'Approval Registration',
    'pending_rejection': 'Pending/Rejection',
    'add_product': 'Add First Product',  
    'onboarding_rejection_pending': 'Onboarding Rejection and Pending',
    'qc': 'QC Report',
    'product_approval': 'Your Product is Approved',
    'product_pending_rejection':'Your Product is Pending/Rejected',
    'order_notification': 'You have Received a New Order!',
    'seller_shipping_status': 'Your Item Has Been Marked as Shipped',
    'message_mentor_seller': 'Welcome message from Chief Mentor Seller School',
    'complete_onboarding': 'Complete Your Onboarding Form',
    'welcome_buyers': 'Welcome to Zite69!-Buyers',
    'order_details_buyers':'Buyers Order Summary',
}

def get_var_nodes(node):
    ret = set()
    if hasattr(node, 'nodelist'):
        for n in node.nodelist:
            if n.__class__ == VariableNode:
                ret.add(n.token.contents)
            if hasattr(n, 'nodelist'):
                ret.update(get_var_nodes(n))
    return ret

def run(*args):
    cmd = args[0]
    temp = args[1]
    template_name = f"email/{temp}.html"
    template = get_template(template_name)
    variables = set()
    for n in template.template.nodelist:
        variables.update(get_var_nodes(n))
    base_name = template.template.nodelist[0].parent_name.token.strip("'").strip('"')
    print(base_name)
    base = get_template(base_name)
    for n in base.template.nodelist:
        variables.update(get_var_nodes(n))
    variables = list(filter(lambda n: n != 'base_uri' and n != 'block.super' , variables))
    if cmd == 'list':
        print(f"Variables inside {temp}.html: {variables}")
    elif cmd == 'send':
        ctx = {}
        ctx['base_uri'] = 'https://www.zite69.com'
        if len(variables) + 2 != len(args):
            print(f"Please specify all variable values: {variables}")
            return
        for i, v in enumerate(variables):
            if '.' not in v:
                ctx[v] = args[2+i]
            else:
                obj, prop = v.split(".")
                if obj not in ctx:
                    ctx[obj] = {}
                ctx[obj][prop] = args[2+i]
        ctx['template'] = template_name
        if temp in MAP_TO_SUBJECT:
            ctx['subject'] = MAP_TO_SUBJECT[temp]
        else:
            ctx['subject'] = 'Please update scripts/test_email.py to add to MAP_TO_SUBJECT'
        if ',' in settings.SEND_TEST_EMAIL:
            toaddr, cc = settings.SEND_TEST_EMAIL.split(",")
        else:
            toaddr = settings.SEND_TEST_EMAIL
            cc = ""
        if cc != "":
            ctx['cc'] = [cc]
        resp = send_email(toaddr, **ctx)
        if resp == 1:
            print("Sent email successfully")
        else:
            print(f"Failed to send email. Response code: {resp}")
