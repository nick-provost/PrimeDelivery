from django.views.generic import TemplateView
from accounts.models import *
from django.shortcuts import render

#class IndexPageView(TemplateView):
#    template_name = 'main/index.html'

def IndexPageView(request):
    if(request.user.username):
        my_sponsors = Application.objects.filter(user=request.user, status="approved")
        point_history = PointsAudit.objects.filter(awarded_to=request.user.username)
        alerts = Alert.objects.filter(receiver=request.user)
        if request.user.role_name == "driver":
            return render(request, 'layouts/default/driverHome.html', {'my_sponsors':my_sponsors, 'point_history':point_history, 'alerts':alerts})
        elif request.user.role_name=="sponsor":
            this_sponsor = UserAccount.objects.get(username=request.user.username).sponsor
            all_points = set()
            for audit in PointsAudit.objects.all():
                this_user = UserAccount.objects.get(username=audit.awarded_by)
                if(this_user.sponsor == this_sponsor):
                    all_points.add(audit.pk)
            all_points_this_sponsor = PointsAudit.objects.filter(pk__in = all_points)
            print(all_points_this_sponsor);
            return render(request, 'layouts/default/sponsorHome.html', {'all_points':all_points_this_sponsor})
        else:
            all_sales = Order.objects.all()
            all_apps = ApplicationAudit.objects.all()
            all_points = PointsAudit.objects.all()
            all_pass_changes = PasswordChangeAudit.objects.all()
            all_login_attempts = LoginAudit.objects.all()
            return render(request, 'layouts/default/adminHome.html', { 'all_sales' : all_sales, 'all_apps' : all_apps, 'all_points' : all_points, 'all_pass_changes' : all_pass_changes, 'all_login_attempts' : all_login_attempts})
    else:
        return render(request, 'main/index.html')
    
class ChangeLanguageView(TemplateView):
    template_name = 'main/change_language.html'
