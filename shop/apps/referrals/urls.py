from django.urls import path
from shop.apps.referrals.views import (
    ProcessReferralView,
    ReferralDashboardView,
    ReferralLinkForUrlView,
)

app_name = "referrals"

urlpatterns = [
    path("r/<str:code>/", ProcessReferralView.as_view(), name="process_referral"),
    path("dashboard/", ReferralDashboardView.as_view(), name="dashboard"),
    path("link/", ReferralLinkForUrlView.as_view(), name="link-for-url"),
]
