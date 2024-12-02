import requests

def get_ifsc_details(ifsc):
    RAZORPAY_URL = "https://ifsc.razorpay.com/"

    return requests.get(RAZORPAY_URL+ifsc).json()
