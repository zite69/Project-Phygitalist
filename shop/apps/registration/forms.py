from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.password_validation import validate_password, password_validators_help_text_html
from django.contrib.auth import login
from djangocms_form_builder import verbose_name
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import ValidationError as PhoneValidationError
from django.core.exceptions import ValidationError
from shop.apps.main.utils.sms import send_phone_otp
from shop.apps.main.utils.email import send_email_otp
from shop.apps.otp.utils import generate_otp
from django.forms.widgets import Widget
from django.urls import reverse_lazy
from shop.apps.main.errors import ConfigurationError
from shop.apps.otp.utils import authenticate_otp
from shop.apps.user.models import Profile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Submit, Layout, Row, Column, Div, Field
from crispy_forms.bootstrap import AppendedText, StrictButton, InlineRadios
from localflavor.in_.forms import INPANCardNumberFormField
from .models import SellerRegistration, SellerProduct
from shop.apps.main.models import Pincode
from shop.apps.seller.models import Seller
from collections import defaultdict

import logging

logger = logging.getLogger("shop.apps.registration.forms")

User = get_user_model()


class FormWithRequest(forms.Form):

    class Media:
        css = {
            "all": ("css/registration.css",)
        }

    def __init__(self, *args, request=None, **kwargs):
        if request == None:
            raise ConfigurationError(_("Django request must be passed when creating this form instance"))
        super().__init__(*args, **kwargs)
        self.request = request
        self.helper = FormHelper()
        self.helper.form_id = self.__class__.form_id
        self.helper.form_method = 'post'
        self.helper.include_media = False

        self.helper.add_input(Submit(name='submit', value=self.__class__.submit_label,
            css_class="action-btn", css_id=f"submit-{self.__class__.form_name}"))

    def get_user(self):
        if self.request.user.is_authenticated:
            return self.request.user

        user_id = self.request.session.get('user_id', -1)
        if user_id == -1:
            raise ValidationError(_("System failure user not found in session"))
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError(_("System failure wrong user id passed in session"))

        return user

    def upload_files(self):
        return hasattr(self.__class__, 'file_upload') and self.__class__.file_upload == True

class InputWithJavascriptCodeLinkWidget(Widget):
    template_name = "registration/widgets/inputlink.html"

    class Media:
        js = ["js/inputlink.js"]

    def __init__(self, attrs=None, form=None):
        super().__init__(attrs)
        self.form = form

    # def render(self, name, value, attrs=None, renderer=None):
    #     return super().render(name, value, attrs, renderer)

class BootstrapButton(Widget):
    template_name = "registration/widgets/button.html"

    def __init__(self, name, value, attrs=None):
        super().__init__(attrs)

class UserName(FormWithRequest):
    form_id = 'id_form_username'
    form_name = 'username'
    submit_label = 'Register Now'

    name = forms.CharField(label="", max_length=255, required=True, widget=forms.TextInput(attrs={"placeholder": "Your name"}))
    username = forms.CharField(label="", max_length=64, required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "Select username",
            "class": "username",
            "data-validate": reverse_lazy("registration:username_available"),
            "data-action": "none"
        }))

    class Media:
        js = ("js/username.js",)

    # def __init__(self, *args, request=None, **kwargs):
    #     super().__init__(*args, request=request, **kwargs)
    #     self.helper = FormHelper()
    #     self.helper.form_id = 'id_form_username'
    #     self.helper.form_method = 'post'
    #     self.helper.include_media = False

    #     self.helper.add_input(Submit(name='submit', value='Register Now', css_class="action-btn", css_id="submit-username"))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
            raise ValidationError(_("Username is not available. Please choose another"))
        except User.DoesNotExist:
            pass
        return username

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username', '')
        name = cleaned_data.get('name', '')
        first, *last = name.split(" ")
        last = " ".join(last)
        if username != '':
            #this should never happen since the field is a required field
            #this does apparently happen because clean in turns calls clean on the fields and these actions bubble
            #through
            user = User.objects.create(username=username, first_name=first, last_name=last, is_active=False)
            user.save()
            logger.debug(f"Saved user {user}")
            self.request.session['user_id'] = user.id
            logger.debug("Saved user_id in session")

        return cleaned_data

class UserNameNumberEmail(forms.Form):
    name = forms.CharField(label="", max_length=255, required=True, widget=forms.TextInput(attrs={"placeholder": "Your full name"}))
    username = forms.CharField(label="", max_length=64, required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "Please choose your username",
            "class": "username",
            "data-validate": reverse_lazy("registration:username_available")
        }))
    #phone = PhoneNumberField(label="", region='IN', required=True, widget=forms.TextInput(attrs={"placeholder": "Mobile number"}))
    phone = PhoneNumberField(label="", region='IN', required=True,
        widget=InputWithJavascriptCodeLinkWidget(attrs={
            "placeholder": "Phone number",
            "type": "phone",
            "getcode": reverse_lazy("registration:phone_otp")
        }))

    phone_otp = forms.CharField(label="", max_length=10, widget=forms.TextInput(attrs={"placeholder": "Mobile OTP Code"}))
    email = forms.EmailField(label="", required=True, widget=forms.EmailInput(attrs={"placeholder": "Email address"}))
    email_otp = forms.CharField(label="", max_length=10, widget=forms.TextInput(attrs={"placeholder": "Email OTP"}))

    class Media:
        css = {
           "all": ["css/seller.css"]
        }

        js = ["js/seller.js"]

    def clean(self):
        form_data = super().clean()
        phone = form_data.get('phone', None)
        name = form_data.get('name', '')
        if phone == None:
            raise PhoneValidationError(_("Please enter a valid phone number"))
        if name == '':
            raise ValidationError(_("Please enter your name"))

        logging.debug(f"Got phone: {phone} and name: {name}")
        if User.objects.filter(phone=phone).exists():
            raise PhoneValidationError(_("This phone number already exists in our database. Please login with the phone number and password"))

        first, last = name.split(" ")
        user = User(first_name=first, last_name=last, phone=phone, is_active=False)
        user.save()
        logger.debug(f"Got user: {user}")
        otp = generate_otp(user, phone = phone)
        logger.debug(f"Generated otp: {otp}")
        resp = send_phone_otp(phone = phone, otp = otp)
        logger.debug(f"Response from send sms: {resp}")

class PasswordForm(FormWithRequest):
    form_id = 'id_form_password'
    form_name = 'password'
    submit_label = 'Set Password'

    password = forms.CharField(label="", required=True, widget=forms.PasswordInput(attrs={
        "placeholder": "Please enter a password of at least 8 characters containing alphabets and numbers"
    }))

    password2 = forms.CharField(label="", required=True, widget=forms.PasswordInput(attrs={
        "placeholder": "Please enter the same password again to confirm"
    }))

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)
        self.helper.layout = Layout(
            HTML('Create Password'),
            HTML(password_validators_help_text_html()),
            'password',
            'password2'
        )

    def clean(self):
        form_data = self.cleaned_data
        password = form_data.get('password', '').strip()
        password2 = form_data.get('password2', '').strip()
        user = self.get_user()
        if not user:
            raise ValidationError(_("System error: Unable to retrieve user from session data"))

        if not password or not password2:
            raise ValidationError(_("Passwords cannot be blank"))

        if password != password2:
            raise ValidationError(_("Passwords do not match"))

        validate_password(password, user=user)

        user.set_password(password)
        user.is_active = True
        user.save()

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        return form_data

class MobileAndOtp(FormWithRequest):
    form_id = 'id_form_mobile'
    form_name = 'mobile'
    submit_label = 'Verify Phone OTP'

    phone = PhoneNumberField(label="", region='IN', required=True, widget=InputWithJavascriptCodeLinkWidget(attrs={
        "placeholder": "Your Mobile Number",
        "type": "phone",
        "getcode": reverse_lazy("registration:phone_otp")
    }))
    # phone = PhoneNumberField(label="", region='IN', required=True)
    otp = forms.CharField(label=_("Enter OTP sent to your mobile number"), max_length=10)

    # class Media:
    #     js = ("js/otpverify.js",)

    # def __init__(self, *args, request=None, **kwargs):
    #     super().__init__(*args, request=request, **kwargs)

    #     self.helper = FormHelper()
    #     self.helper.form_id = 'form-id-mobile'
    #     self.helper.form_method = 'post'
    #     self.helper.include_media = False

    #     self.helper.add_input(Submit(name='submit', value="Verify Phone OTP", css_class="action-btn"))
    # def __init__(self, *args, request=None, **kwargs):
    #     super().__init__(*args, request=request, **kwargs)
    #     self.helper.layout = Layout(
    #         AppendedText('phone', mark_safe('<a href="#" class="get-code">get code</a>'), placeholder="Your Mobile Number", active=True),
    #         'otp'
    #     )

    def clean(self):
        form_data = super().clean()
        # user_id = self.request.session.get('user_id', -1)
        # if user_id == -1:
        #     raise ValidationError(_("System failure user not found in session"))

        # try:
        #     user = User.objects.get(id=user_id)
        # except User.DoesNotExist:
        #     raise ValidationError(_("System failure wrong user id passed in session"))
        user = self.get_user()
        if not user:
            #We should have already raised a validation error from within
            #Really we should never be called
            logger.critical("Some configuraton issue. user is passed back empty without ValidatonError being fired")

        otp_code = form_data.get('otp', '')
        if otp_code == '':
            raise ValidationError(_("OTP must be provided"))

        phone = form_data.get('phone', '')
        if phone == '':
            raise ValidationError(_("Phone number is required"))

        logger.debug(f"Phone: {phone} type: {type(phone)}")
        valid_user = authenticate_otp(otp=otp_code, phone=phone, active=user.is_active)
        if not valid_user:
            raise ValidationError(_("Invalid OTP"))

        valid_user.phone_verified = True
        valid_user.save()

        return form_data

class EmailAndOtp(FormWithRequest):
    form_id = 'id_form_email'
    form_name = 'email'
    submit_label = 'Verify your email ID'

    email = forms.EmailField(label="", required=True, widget=InputWithJavascriptCodeLinkWidget(attrs={
        "placeholder": "Email address",
        "type": "email",
        "getcode": reverse_lazy("registration:email_otp")
    }))
    otp = forms.CharField(label=_("Enter OTP sent to your email ID"), max_length=10, widget=forms.TextInput(attrs={"placeholder": "Please enter OTP"}))

    # def __init__(self, *args, request=None, **kwargs):
    #     super().__init__(*args, request=request, **kwargs)

    #     self.helper = FormHelper()
    #     self.helper.form_id = 'form-id-email'
    #     self.helper.form_method = 'post'
    #     self.helper.include_media = False

    #     self.helper.add_input(Submit(name='submit', value="Verify your email ID", css_class="action-btn"))

    def clean(self):
        form_data = super().clean()

        user = self.get_user()
        if not user:
            logger.critical("Error we were called when get_user passed back empty user without triggering ValidationError. This should never happen")

        otp_code = form_data.get('otp', '')
        if otp_code == '':
            raise ValidationError(_("OTP must be provided"))

        email = form_data.get('email', '')
        if email == '':
            raise ValidationError(_("Email address must be provided"))

        logger.debug(f"About to validate otp: {otp_code} with email: {email}")
        valid_user = authenticate_otp(otp=otp_code, email=email, active=user.is_active)
        logger.debug(f"Got back user: {valid_user}")
        if not valid_user:
            raise ValidationError(_("Invalid OTP"))

        logger.debug("Saving validated user")
        valid_user.email_verified = True
        valid_user.save()

        return form_data

class EmailOtp(FormWithRequest):
    otp = forms.CharField(label=_("Enter OTP code"), max_length=10)


class AddBusiness(FormWithRequest):
    form_id = 'id_form_addbusiness'
    form_name = 'addbusiness'
    submit_label = 'Add Business'

class GstPan(FormWithRequest):
    STATUS_CHOICES = [
        ('Y', 'I have GST'),
        ('N', "I don't have GST"),
        ('E', 'I am expemted'),
        ('L', 'I will add later')
    ]
    form_id = 'id_form_gst'
    form_name = 'gst'
    submit_label = 'Sell Now'

    class Media:
        css = {
            "all": ["css/gst.css",],
        }

        js = ["js/gst.js",]

    gstin = forms.CharField(label=_("GST Number"), max_length=15, required=False, widget=forms.TextInput(attrs={
        "placeholder": "GST Number - PIN code should match your selected GST PIN code",
    }))
    pan = INPANCardNumberFormField(label="", required=False, widget=forms.TextInput(attrs={
        "placeholder": "Please enter your registered PAN number",
        "class": "hide"
    }))
    gst_status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect())

    def clean_gstin(self):
        gst = self.cleaned_data.get('gstin', '')

        if gst != "":
            try:
                Profile.objects.get(gstin=gst)
                raise ValidationError(_("This GST already exists in our database. If you have another account please login with it"))
            except Profile.DoesNotExist:
                pass

            try:
                SellerRegistration.objects.get(gstin=gst)
                raise ValidationError(_("This GST already exists in our database. If you have another account please login with it"))
            except SellerRegistration.DoesNotExist:
                pass

        logger.debug(f"Inside clean_gstin: returning gst: {gst}")
        return gst

    def clean_pan(self):
        pan = self.cleaned_data.get('pan', '')

        if pan != "":
            try:
                Profile.objects.get(pan=pan)
                raise ValidationError(_("This PAN already exists in our database. If you have another account please login with it"))
            except Profile.DoesNotExist:
                pass

            try:
                SellerRegistration.objects.get(pan=pan)
                raise ValidationError(_("This PAN already exists in our database. If you have another account please login with it"))
            except SellerRegistration.DoesNotExist:
                pass

        logger.debug(f"Inside clean_pan: {pan}")

        return pan

    def clean(self):
        form_data = super().clean()

        user = self.get_user()
        if not user:
            raise ValidationError(_("User is not being set this session"))

        gst = form_data.get('gstin', '')
        pan = form_data.get('pan', '')
        if gst == '' and pan == '':
            logger.debug(f"Form errors: {self._errors}")
            raise ValidationError(_("You must specify either GST or PAN"))

        SellerRegistration.objects.create(
            name = user.get_full_name(),
            phone = user.phone,
            email = user.email,
            gstin = gst,
            pan = pan,
            user = user
        )
        Profile.objects.create(
            user = user,
            type = Profile.TYPE_BUYER,
            level = 1,
            gstin = gst,
            pan = pan,
        )

        return form_data

class GstCrispy(FormWithRequest):
    STATUS_CHOICES = [
        ('Y', 'I have GST'),
        ('N', "I don't have GST"),
        ('E', 'I am expemted'),
        ('L', 'I will add later')
    ]
    form_id = 'id_form_gst'
    form_name = 'gst'
    submit_label = 'Sell Now'

    gstin = forms.CharField(label=_("Enter GST Number"), max_length=15, required=False, widget=forms.TextInput(attrs={
        "placeholder": "Pincode should match your selected GST pincode",
    }))
    pan = INPANCardNumberFormField(label=_("Enter PAN Number"), required=False, widget=forms.TextInput(attrs={
        "placeholder": "Please enter your registered PAN number",
    }))
    gst_status = forms.ChoiceField(choices=STATUS_CHOICES, initial='Y', widget=forms.RadioSelect)

    class Media:
        css = {
            "all": ["css/gst.css",],
        }

        js = ["js/gst.js",]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Div('gstin', css_id='id-gstin'),
            Div('pan', css_id='id-pan', css_class='hide'),
            Div(
                InlineRadios('gst_status', id='gst-id', template='registration/widgets/radio.html'),
                css_class='radio-group'
            ),
            HTML('<p class="legal-support"><a href="https://wa.me/{{ settings.WHATSAPP_NUMBER }}">Click here</a> to consult with our legal team</p>'),
        )

    def clean_gstin(self):
        gst = self.cleaned_data.get('gstin', '')
        gst_status = self.cleaned_data.get('gst_status', 'Y')

        if gst_status != 'Y':
            return gst

        if gst != "":
            try:
                Profile.objects.get(gstin=gst)
                raise ValidationError(_("This GST already exists in our database. If you have another account please login with it"))
            except Profile.DoesNotExist:
                pass

            try:
                SellerRegistration.objects.get(gstin=gst)
                raise ValidationError(_("This GST already exists in our database. If you have another account please login with it"))
            except SellerRegistration.DoesNotExist:
                pass

        logger.debug(f"Inside clean_gstin: returning gst: {gst}")
        return gst

    def clean_pan(self):
        pan = self.cleaned_data.get('pan', '')
        gst_status = self.cleaned_data.get('gst_status', 'Y')

        if gst_status == 'Y':
            return pan

        if pan != "":
            try:
                Profile.objects.get(pan=pan)
                raise ValidationError(_("This PAN already exists in our database. If you have another account please login with it"))
            except Profile.DoesNotExist:
                pass

            try:
                SellerRegistration.objects.get(pan=pan)
                raise ValidationError(_("This PAN already exists in our database. If you have another account please login with it"))
            except SellerRegistration.DoesNotExist:
                pass

        logger.debug(f"Inside clean_pan: {pan}")

        return pan

    def clean(self):
        form_data = super().clean()

        user = self.get_user()
        if not user:
            raise ValidationError(_("User is not being set this session"))

        gst = form_data.get('gstin', '')
        pan = form_data.get('pan', '')
        if gst == '' and pan == '':
            logger.debug(f"Form errors: {self._errors}")
            if not self._errors:
                raise ValidationError(_("You must specify either GST or PAN"))
        else:
            #Check if the user already has a sellerregistration record created.
            try:
                seller_registration = SellerRegistration.objects.get(user=user)
                seller_registration.phone = user.phone
                seller_registration.email = user.email
                seller_registration.gstin = gst
                seller_registration.pan = pan
                seller_registration.user = user
                seller_registration.save()
            except SellerRegistration.DoesNotExist:
                seller_registration = SellerRegistration.objects.create(
                    name = user.get_full_name(),
                    phone = user.phone,
                    email = user.email,
                    gstin = gst,
                    pan = pan,
                    user = user
                )

            try:
                profile = Profile.objects.get(user=user)
                profile.type = Profile.TYPE_BUYER
                profile.level = 1
                profile.gstin = gst
                profile.pan = pan
                profile.save()
            except Profile.DoesNotExist:
                profile = Profile.objects.create(
                    user = user,
                    type = Profile.TYPE_BUYER,
                    level = 1,
                    gstin = gst,
                    pan = pan,
                )

        return form_data

class PincodeForm(FormWithRequest):
    form_id = 'id_form_pincode'
    form_name = 'pincode'
    submit_label = 'Start'

    pincode = forms.CharField(label=_("Enter Pickup Pincode"), max_length=6, widget=forms.TextInput(attrs={
        "placeholder": "Start typing PIN code to see options",
        "data-autocomplete-uri": reverse_lazy("registration:pincode_search")
    }))
    office = forms.CharField(label=_("Please choose place"), widget=forms.Select(attrs={
        "placeholder": "Place",
        "id": "place_select"
    }))

    class Media:
        css = {
            "all": ["https://code.jquery.com/ui/1.14.0/themes/base/jquery-ui.css"]
        }
        js = ["js/place.js", "https://code.jquery.com/ui/1.14.0/jquery-ui.js"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Div('pincode'),
            HTML('<p>Pincode of the place you will pack and ship your products</p>'),
            Div('office')
        )
    def clean(self):
        form_data = super().clean()
        place = form_data.get('office', '')
        if place == '':
            logger.debug("Place not passed in to the form")
            raise ValidationError(_("Place not passed in"))

        user = self.get_user()
        if not user:
            raise ValidationError(_("User not found in the database"))

        try:
            place_object = Pincode.objects.get(id=int(place))
            user.seller_registration.pincode = place_object
            user.seller_registration.save()
        except Pincode.DoesNotExist:
            logger.critical("Becomes important to notify people that Pincode was not found")
            raise ValidationError(_("Pincode not found in the database"))

        return form_data

class LanguagePreference(FormWithRequest):
    form_id = 'id_form_language'
    form_name = 'language'
    submit_label = 'Add Business'

    #Remove English which is the first entry in the list and add the selection of None
    language = forms.ChoiceField(choices=settings.LANGUAGES[1:] + [['--', _("None")],], widget=forms.RadioSelect())

    def clean(self):
        form_data = super().clean()

        language = form_data.get('language', '--')
        logger.debug(f"Got language: {language}")
        if language == 'no':
            language = '--'

        user = self.get_user()
        if not user:
            raise ValidationError(_("System error: Unable to find user in the session"))
        logger.debug(f"Got back user: {user}")
        logger.debug(f"Setting secondary language to: {language}")
        user.preferences['second_language'] = language.upper()

        return form_data

class ShopDetails(FormWithRequest):
    form_id = 'id_form_shop'
    form_name = 'shop'
    submit_label = 'Add Your First Product'

    class Media:
        js = ["js/shopsetup.js"]

    name = forms.CharField(label="", max_length=64, required=True, widget=forms.TextInput(attrs={
        "placeholder": "You can change it later",
        "id": "shop-name",
    }))

    handle = forms.CharField(label="", max_length=12, required=True, widget=forms.TextInput(attrs={
        "placeholder": "Shop handle",
        "id": "shop-handle",
        "data-editted": False
    }))

    # short_handle = forms.CharField(label="", max_length=12, required=False, widget=forms.TextInput(attrs={
    #     "placeholder": "Shop short handle",
    #     "readonly": True,
    #     "id": "shop-short-handle"
    # }))

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, request=request, **kwargs)
        self.helper.layout = Layout(
            HTML("""{% load static %}
            <div class='success-message'>
                <img src='{% static \'img/seller/icon_success.png\' %}' alt='Zite69'>
                <span>Wow! Your business added successfully</span>
            </div>
            <p>Your Unique Shop Name</p>
            """),
            'name', 'handle'
        )

    def clean_handle(self):
        handle = self.cleaned_data.get('handle')

        if not handle:
            raise ValidationError(_("Handle is required."))

        try:
            SellerRegistration.objects.get(shop_handle=handle)
            raise ValidationError(_("Handle not available, please choose another handle"))
        except SellerRegistration.DoesNotExist:
            pass

        try:
            Seller.objects.get(handle=handle)
            raise ValidationError(_("Handle not available, please choose another handle"))
        except Seller.DoesNotExist:
            pass

        return handle

    # def clean_short_handle(self):
    #     short_handle = self.cleaned_data.get('short_handle')

    #     if not short_handle:
    #         raise ValidationError(_("Short Handle is required."))

    #     try:
    #         SellerRegistration.objects.get(shop_handle__startswith=short_handle)
    #         raise ValidationError(_("Please select another handle, this handle is very similar to another seller's handle"))
    #     except SellerRegistration.DoesNotExist:
    #         pass

    #     try:
    #         Seller.objects.get(handle__startswith=short_handle)
    #         raise ValidationError(_("Please select another handle, this handle is very similar to another seller's handle"))
    #     except Seller.DoesNotExist:
    #         pass

    #     return short_handle

    def clean(self):
        form_data = super().clean()

        user = self.get_user()
        if not user:
            logger.critical("Something wrong with the configuration, unable to see the remote user")
            raise ValidationError(_("Unable to find out the remote user"))

        shop_name = form_data.get('name', '')
        if shop_name == '':
            raise ValidationError(_("Shop name is required. Please select some name, it can be changed later"))

        handle = form_data.get('handle')
        logger.debug(f"handle: {handle}")
        # short_handle = form_data.get('short_handle')
        # logger.debug(f"short_handle: {short_handle}")
        if handle != '':
            user.seller_registration.shop_name = shop_name
            user.seller_registration.shop_handle = handle
            user.seller_registration.save()

        return form_data

class AddProduct(FormWithRequest, forms.ModelForm):
    form_id = 'id_form_product'
    form_name = 'product'
    submit_label = 'Add +'
    file_upload = True

    class Meta:
        model = SellerProduct
        fields = ['image', 'name']

    def save(self, commit=True):
        user = self.get_user()
        if not user:
            raise ValidationError(_("Unable to access user in session"))

        self.instance.seller_reg = user.seller_registration

        return super().save(commit)

class Congrats(FormWithRequest):
    form_id = 'id_form_congrats'
    form_name = 'congrats'
    submit_label = 'Finish Shop Setup'


class Thanks(FormWithRequest):
    form_id = 'id_form_thanks'
    form_name = 'thanks'
    submit_label = 'Go to main shop'


SELLER_REGISTRATION_FORMS = [
    ("username", UserName),
    ("mobile", MobileAndOtp),
    ("email", EmailAndOtp),
    ("password", PasswordForm),
    ("business", AddBusiness),
    ("gst", GstCrispy),
    ("pincode", PincodeForm),
    ("language", LanguagePreference),
    ("shop", ShopDetails),
    ("product1", AddProduct),
    ("product2", AddProduct),
    ("product3", AddProduct),
    ("congrats", Congrats),
    ("thanks", Thanks)
]

#All the keys in the SELLER_REGISTRATION_FORMS above will have the default value of registration/seller.html
#only the specific keys given below will have the custom values
REGISTRATION_FORM_TEMPLATES = defaultdict(lambda: 'registration/seller.html', {
    "business": "registration/business.html",
    #"gst": "registration/gst.html",
    "language": "registration/language.html",
    "congrats": "registration/congrats.html",
    "thanks": "registration/thanks.html"
})
