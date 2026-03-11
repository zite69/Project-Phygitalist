from django.apps import AppConfig


class ReferralsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop.apps.referrals'
    label = 'referrals'

    def ready(self):
        from allauth.account.signals import user_logged_in, user_signed_up
        from django.dispatch import receiver
        from shop.apps.referrals.models import Referral

        @receiver(user_logged_in)
        def on_user_logged_in(request, user, **kwargs):
            """Link any anonymous referral responses from this session to the user."""
            referral = Referral.for_request(request)
            if referral and request.session.session_key:
                referral.link_responses_to_user(user, request.session.session_key)

        @receiver(user_signed_up)
        def on_user_signed_up(request, user, **kwargs):
            """Same as login — link referral responses to the newly created user."""
            referral = Referral.for_request(request)
            if referral and request.session.session_key:
                referral.link_responses_to_user(user, request.session.session_key)
