from django.db import models

class Registration(models.Model):
    name = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    email_phone = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"
