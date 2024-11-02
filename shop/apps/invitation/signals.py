from django.dispatch import Signal

signup_code_used = Signal()
signup_code_sent = Signal()
invite_sent = Signal()
invite_accepted = Signal()
joined_independently = Signal()
