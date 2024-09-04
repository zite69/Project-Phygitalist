from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Otp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(_("OTP Secret"), max_length=16)
    is_verified = models.BooleanField(_("Verified"), default=False)
    to_email = models.BooleanField(_("To Email"), default=False)
    to_phone = models.BooleanField(_("To Phone"), default=False)
    creation_date = models.DateTimeField(_("Created On"), auto_now_add=True)
    changed_date = models.DateTimeField(_("Updated On"), auto_now=True)

    def __str__(self):
        userfield = ""
        if self.to_email:
            userfield = self.user.email
        elif self.to_phone:
            userfield = self.user.phone 
        else:
            userfield = self.user.username

        return f"{userfield} {self.creation_date} {self.is_verified}"

