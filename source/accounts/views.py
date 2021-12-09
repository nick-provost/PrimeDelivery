from django.contrib import messages
from django.template import RequestContext
from django.contrib.auth import login, authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView as BaseLogoutView, PasswordChangeView as BasePasswordChangeView,
    PasswordResetDoneView as BasePasswordResetDoneView, PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django_cryptography.fields import encrypt
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View, FormView
from django.conf import settings

from .utils import (
    send_activation_email, send_reset_password_email, send_forgotten_username_email, send_activation_change_email,
)
from .forms import (
    SignInViaUsernameForm, SignInViaEmailForm, SignInViaEmailOrUsernameForm, SignUpForm,
    RestorePasswordForm, RestorePasswordViaEmailOrUsernameForm, RemindUsernameForm,
    ResendActivationCodeForm, ResendActivationCodeViaEmailForm, ChangeProfileForm, ChangeEmailForm, SponsorCreateForm
)
from .forms import *
from .models import Activation

#ADDED BY NICK
from accounts.forms import UserAccountForm, AwardPointsForm, ShowDriversBySponsorField, ViewOpenApplicationsForm, AlertForm
from accounts.models import *
from django.urls import reverse
from django.shortcuts import render
from django.db import connection
from django.contrib.auth.hashers import make_password
from django.template import RequestContext
#END ADD BY NICK

#add by david
from django.views.generic import TemplateView
#end add by david

#add by david
class HelpView(TemplateView):
    template_name = 'accounts/help.html'

#class AdminCreateSponsorUser(TemplateView):
 #   template_name = 'accounts/create_sponsor_user.html'



#end add by david


class GuestOnlyView(View):
    def dispatch(self, request, *args, **kwargs):
        # Redirect to the index page if the user already authenticated
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().dispatch(request, *args, **kwargs)

def DriverSwitchSponsor(request, company_name):
    sponsor_to_switch_to = SponsorOrganization.objects.get(company_name=company_name)
    app = Application.objects.get(user=request.user, sponsor=sponsor_to_switch_to, status="approved")
    points_to_switch_to = app.points
    this_user = request.user
    this_user.num_of_points = points_to_switch_to
    this_user.sponsor = sponsor_to_switch_to
    this_user.save()
    this_users_sponsors = Application.objects.filter(user=this_user, status="approved")
    point_history = AwardPointsModel.objects.filter(awarded_to=this_user.username)
    this_users_alerts = Alert.objects.filter(receiver=this_user)
    return render(request, 'main/index.html' , {'user': this_user, 'my_sponsors': this_users_sponsors, 'point_history' : point_history, 'alerts' : this_users_alerts })


def viewDrivers(request):
    template_name = 'main/index.html'
    this_user = UserAccount.objects.get(username=request.user.username)
    all_users_same_sponsor = Application.objects.filter(sponsor=this_user.sponsor, status="approved")
    print(all_users_same_sponsor)
    all_users_selected_sponsor = UserAccount.objects.none()
    all_apps = Application.objects.filter(sponsor=this_user.sponsor, status="approved")
    sponsor_org = this_user.sponsor
    form = ShowDriversBySponsorField()
    print(SponsorOrganization.objects.get(company_name=this_user.sponsor.company_name).point_ratio)
    if request.GET.get('sponsor'):
        selected_sponsor = request.GET.get('sponsor')
        sponsor_org = SponsorOrganization.objects.get(company_name=selected_sponsor)
        all_apps = Application.objects.filter(sponsor=sponsor_org, status="approved")
        all_users_selected_sponsor = UserAccount.objects.none()
        current_user = UserAccount.objects.none()
        for app in all_apps:
            current_user = UserAccount.objects.filter(username=app.user.username)
            all_users_selected_sponsor = all_users_selected_sponsor | current_user     
    return render(request, 'layouts/default/viewDrivers.html' , {'user': this_user, 'all_users_same_sponsor': all_users_same_sponsor, 'all_users_selected_sponsor': all_users_selected_sponsor, 'form': form, 'sponsor_org': sponsor_org, 'all_apps':all_apps })

def viewSponsors(request):
    template_name = 'main/index.html'
    this_driver = UserAccount.objects.none()
    all_apps_this_driver = Application.objects.none()
    all_sponsors_selected_user = SponsorOrganization.objects.none()
    if request.GET.get('username'):
        selected_driver = request.GET.get('username')
        this_driver = UserAccount.objects.get(username=selected_driver)
        all_apps_this_driver = Application.objects.filter(user=this_driver, status="approved")
        all_sponsors_selected_user = UserAccount.objects.none()
        current_sponsor = SponsorOrganization.objects.none()
        for app in all_apps_this_driver:
            current_sponsor = SponsorOrganization.objects.filter(company_name=app.sponsor.company_name)
            all_sponsors_selected_user = all_sponsors_selected_user | current_sponsor
    
    form = ShowSponsorsByDriverField()
    return render(request, 'layouts/default/viewSponsors.html' , {'this_driver': this_driver, 'all_sponsors_selected_user': all_sponsors_selected_user, 'form': form, 'all_apps_this_driver':all_apps_this_driver })


def viewApplications(request):
    template_name = 'main/index.html'
    this_user = UserAccount.objects.get(username=request.user.username)
    sponsor_org = this_user.sponsor
    all_open_applications = Application.objects.filter(status="pending")
    all_applications_selected_sponsor = Application.objects.filter(sponsor=sponsor_org, status="pending")
    form = ViewOpenApplicationsForm()
    if request.GET.get('sponsor'):
        selected_sponsor = request.GET.get('sponsor')
        sponsor_org = SponsorOrganization.objects.get(company_name=selected_sponsor)
        all_applications_selected_sponsor = Application.objects.filter(sponsor=sponsor_org, status="pending")
    return render(request, 'layouts/default/viewApplications.html' , {'user': this_user, 'all_open_applications': all_open_applications, 'all_applications_selected_sponsor': all_applications_selected_sponsor, 'form': form, 'sponsor_name': sponsor_org.company_name, 'sponsor':sponsor_org })
       
def ApproveApp(request, username, company_name):
    template_name='main/index.html'
    this_user = UserAccount.objects.get(username=username)
    this_sponsor = SponsorOrganization.objects.get(company_name=company_name)
    this_application = Application.objects.get(user=this_user, sponsor=this_sponsor, status="pending")
    this_application.status = "approved"
    this_application.save()

    alert = Alert.objects.create()
    alert.receiver = this_user
    alert.sender = request.user
    alert.message = "You have been accepted by " + company_name + "."
    alert.save()

    app_audit = ApplicationAudit.objects.create()
    app_audit.driver = this_user
    app_audit.sponsor = this_sponsor
    app_audit.status = "approved"
    app_audit.save()

    this_user.approval_status="approved"
    this_user.save()

    this_user.all_sponsors.add(this_sponsor)
    application_username = username

    approver = UserAccount.objects.get(username=request.user.username)
    all_open_applications = Application.objects.filter(status="pending")
    user_to_be_approved = UserAccount.objects.get(username=application_username)

    messages.success(request, _('Approval Success'))

    return render(request, 'layouts/default/viewApplications.html', {'user':approver, 'all_open_applications':all_open_applications, 'sponsor':company_name })

def DenyApp(request, username, company_name):
    template_name='main/index.html'
    this_user = UserAccount.objects.get(username=username)
    this_sponsor = SponsorOrganization.objects.get(company_name=company_name)
    this_application = Application.objects.get(user=this_user, sponsor=this_sponsor, status="pending")
    this_application.status = "denied"
    this_application.save()

    alert = Alert.objects.create()
    alert.receiver = this_user
    alert.sender = request.user
    alert.message = "You have been denied by " + company_name + "."
    alert.save()

    app_audit = ApplicationAudit.objects.create()
    app_audit.driver = this_user
    app_audit.sponsor = this_sponsor
    app_audit.status = "denied"
    app_audit.save()

    this_user.all_sponsors.add(this_sponsor)
    application_username = username

    approver = UserAccount.objects.get(username=request.user.username)
    all_open_applications = Application.objects.filter(status="pending")
    user_to_be_approved = UserAccount.objects.get(username=application_username)

    messages.success(request, _('Denial Success'))

    return render(request, 'layouts/default/viewApplications.html', {'user':approver, 'all_open_applications':all_open_applications, 'sponsor':company_name })

def DropDriver(request, username, company_name):
    template_name='main/index.html'
    this_user = UserAccount.objects.get(username=username)
    this_sponsor = SponsorOrganization.objects.get(company_name=company_name)
    
    this_application = Application.objects.get(user=this_user, sponsor=this_sponsor, status="approved")
    this_application.status="denied"
    this_application.save()

    alert = Alert.objects.create()
    alert.receiver = this_user
    alert.sender = request.user
    alert.message = "You have been dropped by " + company_name + "."
    alert.save()

    this_user.all_sponsors.remove(this_sponsor)
    application_username = username

    approver = UserAccount.objects.get(username=request.user.username)
    all_open_applications = Application.objects.filter(status="pending")
    user_to_be_approved = UserAccount.objects.get(username=application_username)

    messages.success(request, _('Driver Successfully Dropped'))

    return render(request, 'layouts/default/viewDrivers.html', {'user':approver, 'all_open_applications':all_open_applications, 'sponsor':company_name })


    
def AwardPoints(request, username, company_name):
    driver_username = username
    sponsor_name = company_name
    template_name = 'main/index.html'
    this_user = UserAccount.objects.get(username=request.user.username)
    all_users_same_sponsor = UserAccount.objects.filter(sponsor=this_user.sponsor)
    user_to_add_points_to = UserAccount.objects.get(username=driver_username)
    this_sponsor = SponsorOrganization.objects.get(company_name=sponsor_name)
    app = Application.objects.get(user=user_to_add_points_to, sponsor=this_sponsor, status="approved")

    form = AwardPointsForm()
    if request.method == 'POST':
        form = AwardPointsForm(request.POST)
        if form.is_valid():
            pointsAdded = form.cleaned_data['num_points_awarded']
            user_to_add_points_to.num_of_points += pointsAdded
            obj=form.save(commit=False)
            obj.awarded_to = driver_username
            obj.awarded_by = this_user.username
            obj.new_total = user_to_add_points_to.num_of_points
            obj.reason = form.cleaned_data['reason']
            obj.save()

            points_alert = Alert.objects.create()
            points_alert.receiver = app.user
            points_alert.sender = request.user
            points_alert.type = "points"
            if pointsAdded < 0:
                points_alert.message = request.user.first_name + " " + request.user.last_name + " has deducted " + str(pointsAdded*-1) + " points from " + this_sponsor.company_name + ". You now have " + str(app.points+pointsAdded) + " points for " + this_sponsor.company_name + "."
            else:
                points_alert.message = request.user.first_name + " " + request.user.last_name + " has added " + str(pointsAdded) + " points from " + this_sponsor.company_name + ". You now have " + str(app.points+pointsAdded) + " points for " + this_sponsor.company_name + "."
            points_alert.save()

            app.points += pointsAdded
            app.save()
            user_to_add_points_to.save()
        return render(request, 'layouts/default/viewDrivers.html' , {'user': this_user, 'all_users_same_sponsor': all_users_same_sponsor})
    else:
        form = AwardPointsForm()
        return render(request, 'layouts/default/awardPoints.html' , {'form': form, 'user': this_user, 'all_users_same_sponsor': all_users_same_sponsor, 'username': driver_username, 'user_to_add_points_to': user_to_add_points_to})      


class LogInView(GuestOnlyView, FormView):
    template_name = 'accounts/log_in.html'

    @staticmethod
    
    def get_form_class(**kwargs):
        if settings.DISABLE_USERNAME or settings.LOGIN_VIA_EMAIL:
            return SignInViaEmailForm

        if settings.LOGIN_VIA_EMAIL_OR_USERNAME:
            return SignInViaEmailOrUsernameForm

        return SignInViaUsernameForm

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super().dispatch(request, *args, **kwargs)
    def form_valid(self, form):
        request = self.request
        if not form.is_valid():
            login_audit = LoginAudit.objects.create()
            login_audit.username = request.user.username
            login_audit.result = "success"
            login_audit.save()
        # If the test cookie worked, go ahead and delete it since its no longer needed
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        # The default Django's "remember me" lifetime is 2 weeks and can be changed by modifying
        # the SESSION_COOKIE_AGE settings' option.
        if settings.USE_REMEMBER_ME:
            if not form.cleaned_data['remember_me']:
                request.session.set_expiry(0)

        login(request, form.user_cache)

        redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME))
        url_is_safe = is_safe_url(redirect_to, allowed_hosts=request.get_host(), require_https=request.is_secure())

        if url_is_safe:
            return redirect(redirect_to)
        this_user = UserAccount.objects.get(username=request.user.username)
        all_users_same_sponsor = UserAccount.objects.filter(sponsor=this_user.sponsor)
        this_user.viewing_as = this_user.type_to_revert_to
        this_user.role_name = this_user.type_to_revert_to
        this_user.save()
        this_users_apps = Application.objects.filter(user=this_user)
        this_users_sponsors = Application.objects.filter(user=this_user, status="approved")
        if this_user.role_name=="driver":
            point_history = PointsAudit.objects.filter(awarded_to=this_user.username)
            this_users_alerts = Alert.objects.filter(receiver=this_user)
            if this_users_sponsors:
                login_audit = LoginAudit.objects.create()
                login_audit.username = this_user.username
                login_audit.result = "success"
                login_audit.save()
                return render(request, 'layouts/default/driverHome.html' , {'user': this_user, 'my_sponsors': this_users_sponsors, 'point_history':point_history, 'alerts':this_users_alerts })
            else:
                login_audit = LoginAudit.objects.create()
                login_audit.username = this_user.username
                login_audit.result = "failure"
                login_audit.save()
                messages.error(request, _('ERROR: Your Sponsor has not approved your application yet. Please reach out to your Sponsor and try again later.'))
                return render(request, 'accounts/log_in.html', {'form':form, 'user':this_user, 'my_sponsors': this_users_sponsors})

        elif this_user.approval_status == "approved":
            if this_user.role_name == "sponsor":
                login_audit = LoginAudit.objects.create()
                login_audit.username = this_user.username
                login_audit.result = "success"
                login_audit.save()
                this_sponsor = UserAccount.objects.get(username=request.user.username).sponsor
                all_points = set()
                for audit in PointsAudit.objects.all():
                    this_spon = UserAccount.objects.get(username=audit.awarded_by)
                    if(this_spon.sponsor == this_sponsor):
                        all_points.add(audit.pk)
                all_points_this_sponsor = PointsAudit.objects.filter(pk__in = all_points)
                return render(request, 'layouts/default/sponsorHome.html' , {'user': this_user, 'all_users_same_sponsor': all_users_same_sponsor, 'my_sponsors': this_users_sponsors, 'all_points':all_points_this_sponsor})
            else:
                login_audit = LoginAudit.objects.create()
                login_audit.username = this_user.username
                login_audit.result = "success"
                login_audit.save()
                all_sales = Order.objects.all()
                all_apps = ApplicationAudit.objects.all()
                all_points = PointsAudit.objects.all()
                all_pass_changes = PasswordChangeAudit.objects.all()
                all_login_attempts = LoginAudit.objects.all()
                return render(request, 'layouts/default/adminHome.html' , {'user': this_user, 'all_users_same_sponsor': all_users_same_sponsor, 'my_sponsors': this_users_sponsors, 'all_sales' : all_sales, 'all_apps' : all_apps, 'all_points' : all_points, 'all_pass_changes' : all_pass_changes, 'all_login_attempts' : all_login_attempts})
        else:
            login_audit = LoginAudit.objects.create()
            login_audit.username = this_user.username
            login_audit.result = "failure"
            login_audit.save()
            messages.error(request, _('ERROR: Your Sponsor has not approved your application yet. Please reach out to your Sponsor and try again later.'))
            return render(request, 'accounts/log_in.html', {'form':form, 'user':this_user, 'my_sponsors': this_users_sponsors})

def SignUpView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.sponsor = form.cleaned_data['sponsors'][0]
            user.approval_status = "pending"
            user.role_name = "driver"
            user.viewing_as = "driver"
            user.type_to_revert_to = "driver"
            user.is_email_verified = 1
            user.save()
            sponsors = form.cleaned_data['sponsors']
            for spon in sponsors:
                app = Application.objects.create()
                app.user = user
                app.sponsor = spon
                app.status = "pending"
                app.save()
            form = SignUpForm()
            messages.success(request, _('You have successfully applied for an account! You will be able to log in once your Sponsor approves it.'))
            return render(request, 'accounts/sign_up.html', {'form': form})
    form = SignUpForm()
    all_sponsors = SponsorOrganization.objects.all()
    return render(request, 'accounts/sign_up.html', {'form': form, 'user': request.user, 'all_sponsors':all_sponsors})

#used for drivers applying to additional sponsors
def Apply(request):
    template_name='main/index.html'
    this_user = UserAccount.objects.get(username=request.user.username)
    sponsor_list = SponsorOrganization.objects.all()
    my_sponsors = this_user.all_sponsors.all()
    for sponsor in SponsorOrganization.objects.all():
        if my_sponsors.filter(company_name=sponsor.company_name):
            sponsor_list = sponsor_list.exclude(company_name=sponsor.company_name)           
    if request.method == 'POST':
        form = ApplyForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            application = form.save(commit=False)
            application.user = this_user
            application.sponsor = form.cleaned_data['sponsor']
            application.status = "pending"
            application.save()
            form = ApplyForm()
            app_audit = ApplicationAudit.objects.create()
            app_audit.driver = this_user
            app_audit.sponsor = application.sponsor
            app_audit.status = "pending"
            app_audit.save()
            messages.success(request, _('You have successfully applied for another sponsor! You will be notified once your Sponsor approves it.'))
            return render(request, 'accounts/apply.html', {'form': form})
    form = ApplyForm()
    return render(request, 'accounts/apply.html', {'form': form, 'user': request.user, 'all_sponsors':sponsor_list})

#ADD BY NICK

def swap_type(request):
    if request.POST.get('swapToDriver'):
        user_info = UserAccount.objects.get(username=request.user.username)
        user_info.viewing_as = "driver"
        user_info.type_to_revert_to = user_info.role_name
        user_info.num_of_points = 99999
        user_info.role_name = 'driver'
        user_info.save()
    elif request.POST.get('swapBack'):
        user_info = UserAccount.objects.get(username=request.user.username)
        user_info.viewing_as = user_info.type_to_revert_to
        user_info.role_name = user_info.type_to_revert_to
        user_info.num_of_points = 0
        user_info.save()
    elif request.POST.get('swapToSponsor'):
        user_info = UserAccount.objects.get(username=request.user.username)
        user_info.viewing_as = "sponsor"
        user_info.type_to_revert_to = user_info.role_name
        user_info.role_name = 'sponsor'
        user_info.save()

    return redirect("index")
#END ADD BY NICK

#add by david

def CreateSponsorUser(request):
            form = SponsorCreateForm(request.POST)
            if form.is_valid():
                form.save()
                form = SponsorCreateForm()
            
            context = {
                'form':form
            }

            return render(request, "accounts/create_sponsor_user.html", context)
    

#end add by david 
class ActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        # Activate profile
        user = act.user
        user.is_active_account = True
        user.is_email_verified = True
        user.save()

        # Remove the activation record
        act.delete()

        messages.success(request, _('You have successfully activated your account!'))

        return redirect('accounts:log_in')


class ResendActivationCodeView(GuestOnlyView, FormView):
    template_name = 'accounts/resend_activation_code.html'

    @staticmethod
    def get_form_class(**kwargs):
        if settings.DISABLE_USERNAME:
            return ResendActivationCodeViaEmailForm

        return ResendActivationCodeForm

    def form_valid(self, form):
        user = form.user_cache

        activation = user.activation_set.first()
        activation.delete()

        code = get_random_string(20)

        act = Activation()
        act.code = code
        act.user = user
        act.save()

        send_activation_email(self.request, user.email, code)

        messages.success(self.request, _('A new activation code has been sent to your email address.'))

        return redirect('accounts:resend_activation_code')


class RestorePasswordView(GuestOnlyView, FormView):
    template_name = 'accounts/restore_password.html'

    @staticmethod
    def get_form_class(**kwargs):
        if settings.RESTORE_PASSWORD_VIA_EMAIL_OR_USERNAME:
            return RestorePasswordViaEmailOrUsernameForm

        return RestorePasswordForm

    def form_valid(self, form):
        user = form.user_cache
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if isinstance(uid, bytes):
            uid = uid.decode()

        send_reset_password_email(self.request, user.email, token, uid)

        return redirect('accounts:restore_password_done')


def change_profile(request):
    user = UserAccount.objects.get(username=request.user.username)
    template_name = 'accounts/profile/change_profile.html'
    form_class = ChangeProfileForm
    form = ChangeProfileForm(request.POST, request.FILES)

    if request.method == "POST" and form.is_valid():
        user.age = form.cleaned_data['age']
        user.phone_number = form.cleaned_data['phone_number']
        user.bio = form.cleaned_data['bio']
        user.shipping_address = form.cleaned_data['shipping_address']
        user.city = form.cleaned_data['city']
        user.postal_code = form.cleaned_data['postal_code']
        user.state = form.cleaned_data['state']        
        user.profile_pic = form.cleaned_data['profile_pic']
        user.save()
        print(user.profile_pic)
        newPath = '/static/profile_pics/'+str(user.profile_pic)
        print('new path: ' + newPath)
        cursor = connection.cursor()
        cursor.execute("UPDATE accounts_useraccount SET profile_pic=%s WHERE username=%s", [newPath, user.username])

        messages.success(request, _('Profile data has been successfully updated.'))
        
    
    form = ChangeProfileForm()
    return render(request, 'accounts/profile/change_profile.html', {'form': form})


def alert_settings(request):
    user = UserAccount.objects.get(username=request.user.username)
    points_alerts = user.points_alerts
    order_alerts = user.order_alerts
    order_issue_alerts = user.order_issue_alerts
    return render(request, 'accounts/profile/alert_settings.html', {'points_alerts':points_alerts, 'order_alerts':order_alerts, 'order_issue_alerts':order_issue_alerts})

def toggle_points_alerts(request):
    user = UserAccount.objects.get(username=request.user.username)
    points_alerts = user.points_alerts
    order_alerts = user.order_alerts
    order_issue_alerts = user.order_issue_alerts
    if points_alerts:
        user.points_alerts = False
        user.save()
        messages.success(request, _('Points Alerts Successfully Disabled'))
    else:
        user.points_alerts = True
        user.save()
        messages.success(request, _('Points Alerts Successfully Enabled'))
    return render(request, 'accounts/profile/alert_settings.html', {'points_alerts':points_alerts, 'order_alerts':order_alerts, 'order_issue_alerts':order_issue_alerts})

def toggle_order_alerts(request):
    user = UserAccount.objects.get(username=request.user.username)
    points_alerts = user.points_alerts
    order_alerts = user.order_alerts
    order_issue_alerts = user.order_issue_alerts
    if order_alerts:
        user.order_alerts = False
        user.save()
        messages.success(request, _('Order Alerts Successfully Disabled'))
    else:
        user.order_alerts = True
        user.save()
        messages.success(request, _('Order Alerts Successfully Enabled'))
    return render(request, 'accounts/profile/alert_settings.html', {'points_alerts':points_alerts, 'order_alerts':order_alerts, 'order_issue_alerts':order_issue_alerts})

def toggle_order_issue_alerts(request):
    user = UserAccount.objects.get(username=request.user.username)
    points_alerts = user.points_alerts
    order_alerts = user.order_alerts
    order_issue_alerts = user.order_issue_alerts
    if order_issue_alerts:
        user.order_issue_alerts = False
        user.save()
        messages.success(request, _('Order Issue Alerts Successfully Disabled'))
    else:
        user.order_issue_alerts = True
        user.save()
        messages.success(request, _('Order Issue Alerts Successfully Enabled'))

    return render(request, 'accounts/profile/alert_settings.html', {'points_alerts':points_alerts, 'order_alerts':order_alerts, 'order_issue_alerts':order_issue_alerts})

def change_point_ratio(request):
    user = UserAccount.objects.get(username=request.user.username)
    sponsor = user.sponsor
    form_class = ChangePointRatio
    form = ChangePointRatio(request.POST)
    point_ratio = sponsor.point_ratio
    if request.method == "POST" and form.is_valid():
        new_point_ratio = form.cleaned_data['point_ratio']
        sponsor.point_ratio = new_point_ratio
        sponsor.save()
        messages.success(request, _('Point Ratio Successfully Changed'))
    return render(request, 'accounts/profile/change_point_ratio.html', {'form': form, 'point_ratio' : point_ratio})



class ChangeEmailView(LoginRequiredMixin, FormView):
    template_name = 'accounts/profile/change_email.html'
    form_class = ChangeEmailForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        user = self.request.user
        email = form.cleaned_data['email']

        if settings.ENABLE_ACTIVATION_AFTER_EMAIL_CHANGE:
            code = get_random_string(20)

            act = Activation()
            act.code = code
            act.user = user
            act.email = email
            act.save()

            send_activation_change_email(self.request, email, code)

            messages.success(self.request, _('To complete the change of email address, click on the link sent to it.'))
        else:
            user.email = email
            user.save()

            messages.success(self.request, _('Email successfully changed.'))

        return redirect('accounts:change_email')


class ChangeEmailActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        # Change the email
        user = act.user
        user.email = act.email
        user.save()

        # Remove the activation record
        act.delete()

        messages.success(request, _('You have successfully changed your email!'))

        return redirect('accounts:change_email')


class RemindUsernameView(GuestOnlyView, FormView):
    template_name = 'accounts/remind_username.html'
    form_class = RemindUsernameForm

    def form_valid(self, form):
        user = form.user_cache
        send_forgotten_username_email(user.email, user.username)

        messages.success(self.request, _('Your username has been successfully sent to your email.'))

        return redirect('accounts:remind_username')


class ChangePasswordView(BasePasswordChangeView):
    template_name = 'accounts/profile/change_password.html'

    def form_valid(self, form):
        # Change the password
        this_user = UserAccount.objects.get(username=self.request.user.username)
        this_user.password = form.cleaned_data['new_password1']
        this_user.save()

        #create audit
        pass_change_audit = PasswordChangeAudit.objects.create()
        pass_change_audit.username = this_user.username
        pass_change_audit.type = "Change"
        pass_change_audit.save()

        # Re-authentication
        login(self.request, this_user)

        messages.success(self.request, _('Your password was changed.'))

        return redirect('accounts:change_password')


class RestorePasswordConfirmView(BasePasswordResetConfirmView):
    template_name = 'accounts/restore_password_confirm.html'

    def form_valid(self, form):
        # Change the password
        form.save()


        messages.success(self.request, _('Your password has been set. You may go ahead and log in now.'))

        return redirect('accounts:log_in')


class RestorePasswordDoneView(BasePasswordResetDoneView):
    template_name = 'accounts/restore_password_done.html'


class LogOutView(LoginRequiredMixin, BaseLogoutView):
    template_name = 'accounts/log_out.html'
