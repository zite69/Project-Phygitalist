from django.contrib import admin
from django import forms
from django.core import serializers
from django.contrib.admin.options import csrf_protect_m
from shop.apps.seller.models import Seller
from shop.apps.user.models import User
from image_uploader_widget.widgets import ImageUploaderWidget

import logging

logger = logging.getLogger(__package__)

class SellerAdminForm(forms.ModelForm):
    action = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Seller
        widgets = {
            'gstin_file': ImageUploaderWidget(),
            'pan_file': ImageUploaderWidget(),
            'signature_file': ImageUploaderWidget()
        }

        fields = ['name', 'handle', 'user', 'admin', 'ceo', 
                  'gstin', 'gstin_file', 'gstin_file_verified',
                  'pan', 'pan_file', 'pan_file_verified',
                  'signature_file', 'signature_file_verified', 'approval_notes', 'approved', 'action']

    def hide_group(self, group):
        for fld in ['', '_file', '_file_verified']:
            self.fields[group+fld].widget = forms.HiddenInput()
            self.fields[group+fld].required = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None) 
        self.fields['admin'].required = False
        self.fields['ceo'].required = False

        if not instance:
            return

        if hasattr(instance.user, 'seller_registration') and instance.user.seller_registration.gst_status == 'Y':
            self.hide_group('pan')
        else:
            self.hide_group('gstin')

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change_form_seller.html'
    form = SellerAdminForm
    autocomplete_fields = ['user', 'admin', 'ceo']
    list_display = ('handle', 'user', 'approved')
    search_fields = ('handle', 'user__username', 'user__email', 'user__phone')

    def response_change(self, request, obj):
        if 'action' in request.POST:
            action = request.POST['action']
            logger.debug(f"Got Seller ModelAdmin custom action: {action}")
            if action == 'approved':
                if not obj.user.is_staff:
                    obj.user.is_staff = True
                    obj.user.save()
            elif action == 'rejected':
                if obj.user.is_staff:
                    obj.user.is_staff = False
                    obj.user.save()
        else:
            logger.debug("Did not get any action")

        return super().response_change(request, obj)

    # @csrf_protect_m
    # def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
    #     logger.debug("Inside changeform_view")
    #     logger.debug(request.POST)
    #     action = request.POST.get('action', '')
    #     if action == 'approved':
    #         logger.debug("We got approved")
    #     elif action == 'rejected':
    #         logger.debug("We got rejected")
    #     else:
    #         logger.debug(f"We got unknown action: {action}")

    #     if request.method == 'POST' and '_approve' in request.POST:
    #         logger.debug("Called from custom button")

    #     return super().changeform_view(request, object_id, form_url, extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        if obj:
            context['registration_json'] = serializers.serialize('json', [obj.user.seller_registration])
        return super().render_change_form(request, context, add, change, form_url, obj)
