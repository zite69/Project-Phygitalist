import re
import os

from django.conf import settings
from django.template.loader import get_template
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
    'qc_report': 'QC Report',
    'product_approval': 'Your Product is Approved',
    'product_pending_rejection': 'Your Product is Pending/Rejected',
    'order_notification': 'You have Received a New Order!',
    'seller_shipping_status': 'Your Item Has Been Marked as Shipped',
    'mail_mentor_seller': 'Welcome message from Chief Mentor Seller School',
    'complete_onboarding': 'Complete Your Onboarding Form',
    'welcome_buyers': 'Welcome to Zite69! - Buyers',
    'welcome_paidseller': 'Welcome to Zite69! - Sellers',
    'order_details_buyers': 'Buyers Order Summary',
    'otp': 'Your OTP',
    'verification': 'Verify your email',
    'waitlist': 'You are on our waitlist',
    'seller_approval': 'Seller Registration Status Update',
    'bilingual_welcome_email': 'Product Status Update',
}

# Variables set automatically — don't prompt the user for these
_INTERNAL_VARS = {'base_uri', 'base_url', 'block.super'}


def _extract_vars_from_file(file_path, visited=None):
    """
    Read an MJML/HTML file and extract all {{ variable }} references.
    Follows mj-include paths recursively.
    """
    if visited is None:
        visited = set()
    if file_path in visited:
        return set()
    visited.add(file_path)

    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return set()

    # Match {{ variable }} and {{ object.attribute }}
    found = set(re.findall(r'\{\{\s*([\w.]+)\s*\}\}', content))

    # Follow mj-include paths and collect variables from those files too
    for include_path in re.findall(r'<mj-include\s+path="([^"]+)"', content):
        full_path = os.path.join(settings.BASE_DIR, include_path)
        found.update(_extract_vars_from_file(full_path, visited))

    return found


def _get_variables(temp):
    """Return the set of template variables for a given template name."""
    template_name = f"email/mjml/{temp}.mjml"
    template = get_template(template_name)
    file_path = template.origin.name
    variables = _extract_vars_from_file(file_path)
    variables -= _INTERNAL_VARS
    return variables


def run(*args):
    cmd = args[0]
    temp = args[1]

    variables = _get_variables(temp)

    if cmd == 'list':
        print(f"Variables inside {temp}.mjml: {variables}")

    elif cmd == 'send':
        ctx = {}
        ctx['base_uri'] = 'https://www.zite69.com'
        ctx['base_url'] = 'https://www.zite69.com'

        if len(variables) + 2 != len(args):
            print(f"Please specify all variable values: {variables}")
            return

        for i, v in enumerate(variables):
            if '.' not in v:
                ctx[v] = args[2 + i]
            else:
                obj, prop = v.split('.', 1)
                if obj not in ctx:
                    ctx[obj] = {}
                ctx[obj][prop] = args[2 + i]

        ctx['template'] = temp

        if temp in MAP_TO_SUBJECT:
            ctx['subject'] = MAP_TO_SUBJECT[temp]
        else:
            ctx['subject'] = 'Please update scripts/test_mjml.py to add to MAP_TO_SUBJECT'

        if ',' in settings.SEND_TEST_EMAIL:
            toaddr, cc = settings.SEND_TEST_EMAIL.split(',', 1)
        else:
            toaddr = settings.SEND_TEST_EMAIL
            cc = ''

        if cc:
            ctx['cc'] = [cc]

        resp = send_email(toaddr, **ctx)
        if resp == 1:
            print("Sent email successfully")
        else:
            print(f"Failed to send email. Response code: {resp}")
