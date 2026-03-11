from django.dispatch import Signal

# Fired when an anonymous ReferralResponse is linked to a newly-authenticated user.
# Sender: the Referral instance. Kwargs: response (ReferralResponse instance).
user_linked_to_response = Signal()
