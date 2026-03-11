from django.contrib import admin
from shop.apps.referrals.models import Referral, ReferralResponse


class ReferralResponseInline(admin.TabularInline):
    model = ReferralResponse
    extra = 0
    readonly_fields = ("session_key", "user", "ip_address", "action", "http_referrer", "created_at")
    can_delete = False


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "label", "redirect_to", "response_count", "created_at", "expired_at")
    list_filter = ("label",)
    search_fields = ("code", "user__email", "user__username")
    readonly_fields = ("code", "url", "created_at")
    inlines = [ReferralResponseInline]

    def url(self, obj):
        return obj.url
    url.short_description = "Referral URL"


@admin.register(ReferralResponse)
class ReferralResponseAdmin(admin.ModelAdmin):
    list_display = ("referral", "user", "action", "ip_address", "created_at")
    list_filter = ("action",)
    search_fields = ("referral__code", "user__email", "session_key")
    readonly_fields = ("created_at",)
