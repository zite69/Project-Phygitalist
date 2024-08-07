from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

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
    
    add_fieldsets = UserAdmin.add_fieldsets +(
        (None,{'fields':('phone',),}),
    )
    
    fieldsets = UserAdmin.fieldsets +(
        (None,{'fields':('phone',),}),
    )
