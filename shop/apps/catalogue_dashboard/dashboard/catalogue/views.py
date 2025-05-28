from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import View
from django.contrib import messages
from django.http import JsonResponse
from oscar.apps.dashboard.catalogue import views as originalviews
from shop.apps.catalogue_dashboard.dashboard.catalogue.forms import ProductForm, ProductSearchForm
from shop.apps.catalogue_dashboard.dashboard.catalogue.tables import ProductTable
from shop.apps.catalogue.models import Product, Seller
from shop.apps.main.utils.email import send_products_approved
from rules.contrib.views import PermissionRequiredMixin
import json
from oscar.apps.dashboard.catalogue.views import ProductCreateUpdateView as OGProductCreateUpdateView
from icecream import ic
import logging

logger = logging.getLogger(__package__)

class ProductCreateUpdateView(OGProductCreateUpdateView):
    def dispatch(self, request, *args, **kwargs):
        logger.debug("inside dispatch")
        print("in here!!!")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.debug("Inside ProductCreateUpdateView")
        logger.debug(request.POST)
        if self.object.qc_status == Product.QcStatus.APPROVED:
            self.object.qc_status = Product.QcStatus.NOT_SUBMITTED
            self.object.save()

        return super().post(request, *args, **kwargs)

class ProductQcApproveAll(View):
    def post(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.groups.filter(name='Seller Admin').exists()):
            messages.warning(request, "You are not authorized to Approve these products")
            return HttpResponseRedirect(reverse("dashboard:catalogue-product-list"))

        seller_id = request.POST.get("seller_id", "")
        upc = request.POST.get("upc", "")
        title = request.POST.get("title", "")

        if seller_id != "":
            try:
                seller = Seller.objects.get(id=seller_id)
            except Seller.DoesNotExist:
                messages.warning(request, "Incorrect Seller Provided")
                return HttpResponseRedirect(reverse("dashboard:catalogue-product-list"))

            products_filter = Q(qc_status=Product.QcStatus.SUBMITTED)
            if upc != "":
                products_filter &= Q(upc__icontains=upc)

            if title != "":
                products_filter &= Q(title__icontains=title)
            
            products_qs = seller.products.filter(products_filter)
            products = list(products_qs)
            products_qs.update(qc_status=Product.QcStatus.APPROVED)
            resp = send_products_approved(seller, products)
            logger.debug("Got back response from send_products_approved")
            logger.debug(resp)
            messages.info(request, f"You have approved {len(products)} products for the Seller: {seller.handle}")
            return HttpResponseRedirect(reverse("dashboard:catalogue-product-list"))
        
        messages.warning(request, "You must select a Seller who's products you wish to approve")
        return HttpResponseRedirect(reverse("dashboard:catalogue-product-list"))

def has_permission(user, product):
    return (user.is_superuser or user.groups.filter(name='Seller Admin').exists() 
            or product.seller.user == user or product.seller.admin == user)

class ProductQcApprove(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON Input"})

        product_id = data.get('product_id', '')
        if product_id == '':
            return JsonResponse({"error": "Invalid Product ID was passed"})

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product does not exist"})

        if not has_permission(request.user, product):
            return JsonResponse({"error": "Unauthorized user"})

        status = data.get('status', 'approved')
        logger.debug(f"product: {product} status: {status}")
        if status == 'approved':
            product.qc_status = Product.QcStatus.APPROVED
            resp = send_products_approved(product.seller, [product])
            logger.debug(f"Got back response: {resp} after sending products approved email")
        else:
            product.qc_status = Product.QcStatus.SUBMITTED
        product.save()
        
        return JsonResponse({"message": f"Product QC Status has been updated to {status}"})


class ProductListView(originalviews.ProductListView):
    table_class = ProductTable
    form_class = ProductSearchForm

    def get(self, request, *args, **kwargs):
        # ic("inside catalogue dashboard")
        if not (request.user.is_superuser or request.user.groups.filter(name='Seller Admin').exists()):
            if not hasattr(request.user, 'seller'):
                return redirect('/dashboard/onboarding/')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['seller'] = 'Main Seller'
        # ic("Inside get_context_data")
        # ic(ctx)
        # ic(ctx['products'])
        return ctx


    def apply_search(self, queryset):
        qs = super().apply_search(queryset)
        data = self.form.cleaned_data
        seller = data['seller']

        if seller:
            qs = qs.filter(seller=seller)

        return qs

class ProductCreateRedirectView(originalviews.ProductCreateRedirectView):
    pass

class ProductCreateUpdateView(originalviews.ProductCreateUpdateView, PermissionRequiredMixin):
    form_class = ProductForm
    permission_required = 'products.can_edit_product'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.has_perm('products.can_edit_product', obj):
            raise PermissionDenied
        return obj

    # def get_permission_object(self):
    #     return self.get_object()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user =  self.request.user
        
        if user.is_superuser:
            pass
        elif user.seller_admins.exists():
            form.fields['seller'].queryset = user.seller_admins.all()
        elif hasattr(user, 'seller'):
            form.fields.pop('seller', None)
        
        return form

    def form_valid(self, form):
        user = self.request.user

        if hasattr(user, 'seller'):
            form.instance.seller = user.seller

        return super().form_valid(form)

class ProductDeleteView(originalviews.ProductDeleteView):
    pass

class StockAlertListView(originalviews.StockAlertListView):
    pass


class CategoryListView(originalviews.CategoryListView):
    pass


class CategoryDetailListView(originalviews.CategoryDetailListView):
    pass


class CategoryListMixin(originalviews.CategoryListMixin):
    pass


class CategoryCreateView(originalviews.CategoryCreateView):
    pass


class CategoryUpdateView(originalviews.CategoryUpdateView):
    pass


class CategoryDeleteView(originalviews.CategoryDeleteView):
    pass


class ProductLookupView(originalviews.ProductLookupView):
    pass


class ProductClassCreateUpdateView(originalviews.ProductClassCreateUpdateView):
    pass

class ProductClassCreateView(originalviews.ProductClassCreateView):
    pass
    # form_class = ProductClassForm

    # def __init__(self, *args, **kwargs):
    #     ic("Inside __init__")
    #     ic(*args)
    #     ic(**kwargs)
    #     super().__init__(*args, **kwargs)

    # def get_form(self, form_class=None):
    #     form = super().get_form(form_class)
    #     user = self.request.user
    #     if user.is_superuser:
    #         pass
    #     elif hasattr(user, 'seller_admins') and user.seller_admins.exists():
    #         form.fields['seller'].queryset = user.seller_admins.all()
    #     elif hasattr(user, 'seller'):
    #         form.fields.pop('seller', None)

    #     return form

    # def form_valid(self, form):
    #     user = self.request.user

    #     if hasattr(user, 'seller'):
    #         form.instance.seller = user.seller

    #     return super().form_valid(form)

    # def get(self, request, *args, **kwargs):
    #     ic("inside get")
    #     ic(*args)
    #     ic(**kwargs)
    #     return super().get(request, *args, **kwargs)

    # def get_context_data(self, *args, **kwargs):
    #     ctx = super().get_context_data(*args, **kwargs)
    #     ic("inside get_context_data")
    #     ic(self.form_class.__module__)
    #     ic(ctx)
    #     return ctx



class ProductClassUpdateView(originalviews.ProductClassUpdateView):
    pass


class ProductClassListView(originalviews.ProductClassListView):
    pass
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     ic(self.request.user)
    #     # if user is superuser then don't filter any of the Product Classes
    #     if self.request.user.is_superuser or self.request.user.groups.filter(name='Seller Admin').exists():
    #         return qs
    #     if hasattr(self.request.user, 'seller'):
    #         qs.filter(Q(seller__id=1) | Q(seller__id=self.request.user.seller.id))
    #         return qs
    #     if self.request.user.seller_admins.count() > 0:
    #         qs.filter(Q(seller__id=1) | Q(seller__admin=self.request.user))
    #         return qs
    #     return qs.none()


class ProductClassDeleteView(originalviews.ProductClassDeleteView):
    pass


class AttributeOptionGroupCreateUpdateView(originalviews.AttributeOptionGroupCreateUpdateView):
    pass


class AttributeOptionGroupCreateView(originalviews.AttributeOptionGroupCreateView):
    pass


class AttributeOptionGroupUpdateView(originalviews.AttributeOptionGroupUpdateView):
    pass


class AttributeOptionGroupListView(originalviews.AttributeOptionGroupListView):
    pass


class AttributeOptionGroupDeleteView(originalviews.AttributeOptionGroupDeleteView):
    pass


class OptionListView(originalviews.OptionListView):
    pass

class OptionCreateUpdateView(originalviews.OptionCreateUpdateView):
    pass


class OptionCreateView(originalviews.OptionCreateView):
    pass


class OptionUpdateView(originalviews.OptionUpdateView):
    pass


class OptionDeleteView(originalviews.OptionDeleteView):
    pass

