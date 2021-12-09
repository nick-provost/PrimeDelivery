from datetime import timedelta
from django_cryptography.fields import encrypt
from django import forms
from django.forms import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import *


class UserCacheMixin:
    user_cache = None


class SignIn(UserCacheMixin, forms.Form):
    password = forms.CharField(label=_('Password'), strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.USE_REMEMBER_ME:
            self.fields['remember_me'] = forms.BooleanField(label=_('Remember me'), required=False)

    def clean_password(self):
        password = self.cleaned_data['password']

        if not self.user_cache:
            return password

        if not self.user_cache.check_password(password):
            login_audit = LoginAudit.objects.create()
            login_audit.username = self.cleaned_data['email_or_username']
            login_audit.result = "failure"
            login_audit.save()
            raise ValidationError(_('You entered an invalid password.'))
        return password


class SignInViaUsernameForm(SignIn):
    username = forms.CharField(label=_('Username'))

    @property
    def field_order(self):
        if settings.USE_REMEMBER_ME:
            return ['username', 'password', 'remember_me']
        return ['username', 'password']

    def clean_username(self):
        username = self.cleaned_data['username']

        user = UserAccount.objects.filter(username=username).first()
        if not user:
            raise ValidationError(_('You entered an invalid username.'))

        if not user.is_active:
            raise ValidationError(_('This account is not active.'))

        self.user_cache = user

        return username


class SignInViaEmailForm(SignIn):
    email = forms.EmailField(label=_('Email'))

    @property
    def field_order(self):
        if settings.USE_REMEMBER_ME:
            return ['email', 'password', 'remember_me']
        return ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data['email']

        user = UserAccount.objects.filter(email__iexact=email).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address.'))

        if not user.is_active:
            raise ValidationError(_('This account is not active.'))

        self.user_cache = user

        return email


class SignInViaEmailOrUsernameForm(SignIn):
    email_or_username = forms.CharField(label=_('Email or Username'))

    @property
    def field_order(self):
        if settings.USE_REMEMBER_ME:
            return ['email_or_username', 'password', 'remember_me']
        return ['email_or_username', 'password']

    def clean_email_or_username(self):
        email_or_username = self.cleaned_data['email_or_username']

        user = UserAccount.objects.filter(Q(username=email_or_username) | Q(email__iexact=email_or_username)).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address or username.'))

        if not user.is_active_account:
            raise ValidationError(_('This account is not active.'))

        self.user_cache = user

        return email_or_username


class SignUpForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['sponsors', 'role_name', 'first_name', 'last_name', 'phone_number', 'email', 'username', 'password', 'approval_status']

    sponsors = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=SponsorOrganization.objects.all())
    role_name = forms.CharField(widget=forms.HiddenInput(), required = False)
    first_name = forms.CharField(label='First Name', max_length=25)
    last_name = forms.CharField(label='Last Name', max_length=25)
    phone_number = forms.CharField(label='Phone Number', max_length=10)
    email = forms.EmailField(label=_('Email'))
    username = forms.CharField(label='User Name', max_length=60)
    
    password = forms.CharField(label='Password', max_length=25, widget=forms.PasswordInput())
    
    approval_status = forms.CharField(widget=forms.HiddenInput(), required = False)

    def clean_email(self):
        email = self.cleaned_data['email']

        user = UserAccount.objects.filter(email__iexact=email).exists()
        if user:
            raise ValidationError(_('You can not use this email address.'))

        return email


class ApplyForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['sponsor']

    sponsor = forms.ModelChoiceField(queryset=SponsorOrganization.objects.all())

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ['receiver', 'message']

    receiver = forms.ModelChoiceField(queryset=UserAccount.objects.filter(role_name="driver").values_list("username", flat=True).distinct())
    message = forms.CharField(label='Message', max_length=250)


#ADDED BY NICK
class UserAccountForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'username', 'password']

    first_name = forms.CharField(label='First Name', max_length=25)
    last_name = forms.CharField(label='Last Name', max_length=25)
    phone_number = forms.CharField(label='Phone Number', max_length=10)
    username = forms.CharField(label='User Name', max_length=60)
    email = forms.EmailField(label='Email Address', help_text='Required. Enter an existing email address')
    password = forms.CharField(label='Password', max_length=25, widget=forms.PasswordInput())
    #profile_pic = forms.FileField(label='Upload a Profile Picture')


    def __init__(self, *args, **kwargs):
        super(UserAccountForm, self).__init__(*args, **kwargs)
        for _field__name, field in self.fields.items():
            field.required = True


class AwardPointsForm(forms.ModelForm):
    class Meta:
        model = PointsAudit
        fields = ['num_points_awarded', 'reason']

    num_points_awarded = forms.IntegerField(label='Points Awarded')
    reason = forms.CharField(label='Reason', max_length=250)

class ShowDriversBySponsorField(forms.ModelForm):
    class Meta:
        model = SponsorOrganization
        fields = ['sponsor']
    sponsor = forms.ModelChoiceField(queryset=SponsorOrganization.objects.values_list("company_name", flat=True).distinct())

class ShowSponsorsByDriverField(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['username']
    username = forms.ModelChoiceField(queryset=UserAccount.objects.filter(role_name="driver").values_list("username", flat=True).distinct())


class ViewOpenApplicationsForm(forms.ModelForm):
    class Meta:
        model = SponsorOrganization
        fields = ['sponsor']
    sponsor = forms.ModelChoiceField(queryset=SponsorOrganization.objects.values_list("company_name", flat=True).distinct())

class ChangePointRatio(forms.ModelForm):
    class Meta:
        model = SponsorOrganization
        fields = ['point_ratio']

    point_ratio = forms.IntegerField(label='Point Ratio')

#END ADD BY NICK

#startadd david - sponsorcreate

class SponsorCreateForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['role_name', 'first_name', 'last_name', 'phone_number', 'email', 'username', 'password']

    first_name = forms.CharField(label='First Name', max_length=25)
    last_name = forms.CharField(label='Last Name', max_length=25)
    phone_number = forms.CharField(label='Phone Number', max_length=10)
    username = forms.CharField(label='User Name', max_length=60)
    email = forms.EmailField(label='Email Address', help_text='Required. Enter an existing email address')
    password = forms.CharField(label='Password', max_length=25, widget=forms.PasswordInput())

#endadd david


#START ADD BY Cameron
#END ADD BY CAMERON


class ResendActivationCodeForm(UserCacheMixin, forms.Form):
    email_or_username = forms.CharField(label=_('Email or Username'))

    def clean_email_or_username(self):
        email_or_username = self.cleaned_data['email_or_username']

        user = UserAccount.objects.filter(Q(username=email_or_username) | Q(email__iexact=email_or_username)).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address or username.'))

        if user.is_active:
            raise ValidationError(_('This account has already been activated.'))

        activation = user.activation_set.first()
        if not activation:
            raise ValidationError(_('Activation code not found.'))

        now_with_shift = timezone.now() - timedelta(hours=24)
        if activation.created_at > now_with_shift:
            raise ValidationError(_('Activation code has already been sent. You can request a new code in 24 hours.'))

        self.user_cache = user

        return email_or_username


class ResendActivationCodeViaEmailForm(UserCacheMixin, forms.Form):
    email = forms.EmailField(label=_('Email'))

    def clean_email(self):
        email = self.cleaned_data['email']

        user = UserAccount.objects.filter(email__iexact=email).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address.'))

        if user.is_active:
            raise ValidationError(_('This account has already been activated.'))

        activation = user.activation_set.first()
        if not activation:
            raise ValidationError(_('Activation code not found.'))

        now_with_shift = timezone.now() - timedelta(hours=24)
        if activation.created_at > now_with_shift:
            raise ValidationError(_('Activation code has already been sent. You can request a new code in 24 hours.'))

        self.user_cache = user

        return email


class RestorePasswordForm(UserCacheMixin, forms.Form):
    email = forms.EmailField(label=_('Email'))

    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address.'))

        if not user.is_active:
            raise ValidationError(_('This account is not active.'))

        self.user_cache = user

        return email


class RestorePasswordViaEmailOrUsernameForm(UserCacheMixin, forms.Form):
    email_or_username = forms.CharField(label=_('Email or Username'))

    def clean_email_or_username(self):
        email_or_username = self.cleaned_data['email_or_username']

        user = UserAccount.objects.filter(Q(username=email_or_username) | Q(email__iexact=email_or_username)).first()
        if not user:
            raise ValidationError(_('You entered an invalid email address or username.'))

        if not user.is_active:
            raise ValidationError(_('This account is not active.'))

        self.user_cache = user

        return email_or_username


class ChangeProfileForm(forms.Form):
    class Meta:
        model = UserAccount
        fields = ['age', 'phone_number', 'bio', 'shipping_address', 'city', 'state', 'postal_code', 'profile_pic']
    STATES = (
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'),
        ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('DC', 'District of Columbia'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'),
        ('IA', 'Iowa'), ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'),
        ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'),
        ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'),
        ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming')
    )

    age = forms.IntegerField(label=_('Age'), required=False)
    phone_number = forms.CharField(label=_('Phone Number'), max_length=10, required=False)
    bio = forms.CharField(label=_('Bio'), max_length=250, required=False)
    shipping_address = forms.CharField(label=_('Shipping Address'), max_length=250, required=False)
    city = forms.CharField(label=_('City'), max_length=25, required=False)
    state = forms.ChoiceField(label=_('State'), choices=STATES)
    postal_code = forms.IntegerField(label=_('Postal Code'), required=False)
    profile_pic = forms.FileField()

class ChangeEmailForm(forms.Form):
    email = forms.EmailField(label=_('Email'))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        if email == self.user.email:
            raise ValidationError(_('Please enter another email.'))

        user = UserAccount.objects.filter(Q(email__iexact=email) & ~Q(id=self.user.id)).exists()
        if user:
            raise ValidationError(_('You can not use this mail.'))

        return email


class RemindUsernameForm(UserCacheMixin, forms.Form):
    email = forms.EmailField(label=_('Email'))
from datetime import timedelta

from django import forms
from django.forms import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import *
