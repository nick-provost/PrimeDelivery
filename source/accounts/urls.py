from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

from main.views import IndexPageView, ChangeLanguageView

from accounts.views import *
from . import views

app_name = 'accounts'

urlpatterns = [

    #add by david

    path('help/', HelpView.as_view(), name='help'),

    path('admin/create-sponsor/', CreateSponsorUser, name='create-sponsor'),


    #end add by david 
    
    path('', IndexPageView, name='index'),

    path('swap_type', views.swap_type, name = 'swap_type'),

    path('log-in/', LogInView.as_view(), name='log_in'),
    path('log-out/', LogOutView.as_view(), name='log_out'),

    path('resend/activation-code/', ResendActivationCodeView.as_view(), name='resend_activation_code'),

    path('sign-up/', views.SignUpView, name='sign_up'),
    path('activate/', ActivateView.as_view(), name='activate'),
    path('apply/', views.Apply, name='apply'),
    path('sign-up/', views.SignUpView, name='sign_up'),
    path('activate/', ActivateView.as_view(), name='activate'),
    path('restore/password/', RestorePasswordView.as_view(), name='restore_password'),
    path('restore/password/done/', RestorePasswordDoneView.as_view(), name='restore_password_done'),
    path('restore/<uidb64>/<token>/', RestorePasswordConfirmView.as_view(), name='restore_password_confirm'),

    path('remind/username/', RemindUsernameView.as_view(), name='remind_username'),

    path('change/profile/', views.change_profile, name='change_profile'),
    path('change/password/', ChangePasswordView.as_view(), name='change_password'),
    path('change/email/', ChangeEmailView.as_view(), name='change_email'),
    path('change/email/<code>/', ChangeEmailActivateView.as_view(), name='change_email_activation'),
    path('alerts/', views.alert_settings, name='alert_settings'),
    path('togglePointsAlerts/', views.toggle_points_alerts, name='toggle_points_alerts'),
    path('toggleOrderAlerts/', views.toggle_order_alerts, name='toggle_order_alerts'),
    path('toggleOrderIssueAlerts/', views.toggle_order_issue_alerts, name='toggle_order_issue_alerts'),

    path('changePointRatio/', views.change_point_ratio, name='change_point_ratio'),
    path('viewDrivers/', views.viewDrivers, name='view_drivers'),
    path('viewSponsors/', views.viewSponsors, name='view_sponsors'),
    path('viewApplications/', views.viewApplications, name="view_applications"),
    path('approveApp/<username>/<company_name>', views.ApproveApp, name='approve_app'),
    path('denyApp/<username>/<company_name>', views.DenyApp, name='deny_app'),
    path('dropDriver/<username>/<company_name>', views.DropDriver, name='drop_driver'),

    path('awardPoints/<username>/<company_name>', views.AwardPoints, name='award_points'),
    path('DriverSwitchSponsor/<company_name>', views.DriverSwitchSponsor, name='driver_switch_sponsor'),
    path('approveApp/<username>/<company_name>', views.ApproveApp, name='approve_app'),
    path('denyApp/<username>/<company_name>', views.DenyApp, name='deny_app'),

    path('awardPoints/<username>', views.AwardPoints, name='award_points'),
]
urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

