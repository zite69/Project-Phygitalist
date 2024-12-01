from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import SellerRegistration, SellerProduct
from image_uploader_widget.admin import ImageUploaderInline
from shop.apps.main.utils.email import send_seller_approval
import logging

logger = logging.getLogger("shop.apps.registration")

class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = SellerRegistration
        fields = ['name', 'shop_name', 'shop_handle', 'phone', 'email', 'gstin', 'gstin_verified', 'pan', 'pan_verified', 'approval_status', 'approval_notes']
        readonly_fields = ['get_pincode']

        widgets = {
                'gst_status': forms.TextInput(attrs={'readonly': 'readonly'}),
                'approval_status': forms.RadioSelect(),
                'gstin_verified': forms.CheckboxInput(),
                'pan_verified': forms.CheckboxInput()
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        logger.debug("Inside form save")
        logger.debug(instance.approval_status)
        if instance.approval_status in (SellerRegistration.STATUS_APPROVED, SellerRegistration.STATUS_REJECTED, SellerRegistration.STATUS_REJECTION_TEMPORARY):
            #Send an email notification
            resp = send_seller_approval(instance.user, instance)
            logger.debug("got response from send_seller_approval:")
            logger.debug(resp)

        if commit:
            instance.save()
        return instance

class SellerProductAdmin(ImageUploaderInline):
    model = SellerProduct
    fields = ['name', 'image']

class ApprovalStatusListFilter(admin.SimpleListFilter):
    title = _("Approval Status")

    parameter_name = "approval_status"

    def lookups(self, request, model_admin):
        return SellerRegistration.STATUS_CHOICES

    def queryset(self, request, queryset):
        filter_value = self.value()
        return queryset.filter(approval_status=filter_value) if filter_value else queryset  

@admin.register(SellerRegistration)
class SellerRegistrationAdmin(admin.ModelAdmin):
    form = SellerRegistrationForm
    inlines = [SellerProductAdmin]
    list_filter = [ApprovalStatusListFilter]
    list_display = ['name', 'shop_handle', 'phone', 'email', 'gstin', 'pan']
    fields = ['name', 'shop_name', 'shop_handle', 'phone', 'email', 
              'gst_status_label', 'gstin', 'gstin_verified', 'pan', 'pan_verified', 
              'get_pincode', 'approval_status', 'approval_notes']
    readonly_fields = ['gst_status_label', 'get_pincode']
    search_fields = ['phone', 'email', 'gstin', 'pan', 'shop_handle']

    @admin.display(description="GST Status")
    def gst_status_label(self, instance):
        for k, v in SellerRegistration.GST_STATUS_CHOICES:
            if instance.gst_status == k:
                return v

        return ""


