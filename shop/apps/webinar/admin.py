from django.contrib import admin
from .models import Registration

#admin.site.register(Registration)
# Register your models here.
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'pincode', 'email_phone']
