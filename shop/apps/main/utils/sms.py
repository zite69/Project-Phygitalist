import requests
import base64
from django.conf import settings
import json

def get_auth_token():
    authkey = settings.SMS_AUTH_KEY
    authtoken = settings.SMS_AUTH_TOKEN

    authheader = f'{authkey}:{authtoken}'
    authheader_bytes = base64.b64encode(authheader.encode())
    authheader_str = authheader_bytes.decode()

    token = f'Basic {authheader_str}'

    return token

def send_otp(number, otp, sms_template):
    token = get_auth_token()

    data = {
        "Text": sms_template,
        "Number": number,
        "SenderId": settings.SMS_SENDER_ID,
        "Tool": "API"
    }

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    SMS_PRODUCTION_URL = f'https://restapi.smscountry.com/v0.1/Accounts/{authkey}/SMSes/'
    SMS_MOCK_URL = f'https://private-anon-ccec9b3d62-smscountryapi.apiary-mock.com/v0.1/Accounts/{authkey}/SMSes/'

    if settings.get("SMS_LIVE", False):
        url = SMS_PRODUCTION_URL
    else:
        url = SMS_MOCK_URL
    
    resp = requests.post(url, data=json.dumps(data), headers=headers)

    return resp.json()