import requests
from django.conf import settings
from .urls import get_site_base_uri

def get_short_url(path):
    base_uri = get_site_base_uri()
    full_uri = f"{base_uri}{path}"
    SHORTENER_URL = f"{settings.ZITE69_SHORTENER_URL}/c"
    AUTH_TOKEN = settings.ZITE69_SHORTENER_TOKEN
    token = f"Token {AUTH_TOKEN}"

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    data = {
        "url": full_uri
    }
    resp = requests.post(SHORTENER_URL, headers=headers, json=data)
    output = resp.json()
    return output['out_url'] if 'out_url' in output else ''
