from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from .forms import Zite69UserCreationForm, Zite69UserChangeForm


@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    model =get_user_model()
    add_form = Zite69UserCreationForm
    form = Zite69UserChangeForm
    list_display = [
        'username',
        'email',
        'phone'
    ]
    list_display_links = [
        'username',
        'email',
        'phone'
    ]

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None,{'fields':('phone', 'email_verified', 'phone_verified' ),}),
    )
    
    fieldsets = UserAdmin.fieldsets + (
        (None,{'fields':('phone', 'email_verified', 'phone_verified'),}),
    )
    
    # def formfield_for_dbfield(self, db_field, **kwargs):
    #     if db_field.name == 'phone':
    #         kwargs['widget'] = PhoneNumberPrefixWidget()
    #     return super().formfield_for_dbfield(db_field, **kwargs)

    # def get_fields(self, request, obj=None):
    #     fields = super().get_fields(request, obj)
    #     fields = list(fields)
    #     fields[fields.index('phone')] = ('phone', 'phone')
    #     return fields
