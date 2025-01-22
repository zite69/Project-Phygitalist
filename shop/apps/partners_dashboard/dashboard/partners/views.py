from oscar.apps.dashboard.partners import views as originalviews
from shop.apps.partners_dashboard.dashboard.partners.forms import PartnerSearchForm, PartnerCreateForm
from icecream import ic

class PartnerListView(originalviews.PartnerListView):
    form_class = PartnerSearchForm

    def get_queryset(self):
        qs = super().get_queryset()
        
        user = self.request.user

        data = self.form.cleaned_data
        ic(data)
        #A Seller only sees their own partners
        if hasattr(user, 'sellers'):
            return qs.filter(sellers__in=[user.seller])

        #An admin for one or more Seller sees the list of all Sellers that they
        #are an admin for
        # if user.seller_admins.exists() and not user.is_superuser:
        #     return qs.filter(seller__in=user.seller_admins.all())

        if data['seller']:
            if self._is_seller_admin() and not user.seller_admins.filter(seller=data['seller']).exists():
                return qs.filter(sellers__in=[user.seller_admins.all()])
            description = f"Partners for seller {data['seller']}"
            qs = qs.filter(sellers__in=[data['seller']])
            if data['name']:
                self.description = description + ":" +  self.description
            else:
                self.description = description
            self.is_filtered = True
        elif self._is_seller_admin():
            return qs.filter(sellers__in=[user.seller_admins.all()])

        return qs

    def _is_seller_admin(self):
        user = self.request.user
        return not user.is_superuser and user.seller_admins.exists()

class PartnerCreateView(originalviews.PartnerCreateView):
    form_class = PartnerCreateForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        user = self.request.user
        
        if user.seller_admins.exists() and not user.is_superuser:
            form.fields['seller'].queryset = user.seller_admins.all()
        elif hasattr(user, 'seller'):
            form.fields.pop('seller', None)

        return form


    def form_valid(self, form):
        user = self.request.user

        if hasattr(user, 'seller'):
            form.instance.seller = user.seller

        return super().form_valid(form)

class PartnerManageView(originalviews.PartnerManageView):
    pass

class PartnerDeleteView(originalviews.PartnerDeleteView):
    pass
