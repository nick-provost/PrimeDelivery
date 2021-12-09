from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.conf import settings
from django_cryptography.fields import encrypt
from django.contrib.auth.hashers import make_password, check_password
import datetime

class SponsorOrganization(models.Model):
    company_name = models.CharField("Company Name", max_length=25, validators=[MinLengthValidator(1)])
    phone_number = models.IntegerField("Phone Number", validators=[MinValueValidator(1000000000), MaxValueValidator(99999999999999)])
    street_address = models.CharField("Company Street Address", max_length=32, validators=[MinLengthValidator(1)])
    city = models.CharField("Company City", max_length=25, validators=[MinLengthValidator(1)])
    state = models.CharField("Company State", max_length=25, validators=[MinLengthValidator(1)])
    zipcode = models.IntegerField("Zip Code", validators=[MinValueValidator(500), MaxValueValidator(99999)])
    point_ratio = models.IntegerField("US Cents to Catalog Points Ratio", default=1)
    about_info = models.CharField("About sponsor", max_length=1000000, default="Enter about me info here")

    def __str__(self):
        """
        function __str__ is used to create a string representation of this class
        Returns:
            str: company name
        """
        return self.company_name


class UserAccount(models.Model):

    def upload_path(self, filename):
        ext = filename.split('.')[-1]
        filename = "profilepic_%s.%s" % (self.username, ext)
        return filename

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    ROLE_NAME_CHOICES = (('driver','Driver'),('sponsor','Sponsor'),('admin','Admin'))
    APPROVAL_STATUS_CHOICES = (('pending','Pending'),('approved','Approved'),('denied','Denied'))

    email = models.EmailField('E-Mail', max_length=60, unique=True, default="N/A")
    username = models.CharField('Username', max_length=60, unique=True, default="N/A")
    age = models.IntegerField('Age', blank=True, null=True)
    date_joined = models.DateTimeField('Date Joined', auto_now_add=True)
    num_of_points = models.IntegerField('Points', default=0)
    password = models.CharField('Password', max_length=25, default="NOT_SET")
    #password = encrypt(models.CharField('Password', max_length=25, default="NOT_SET"))
    bio = models.CharField('Bio', max_length=250, null=True)
    shipping_address = models.CharField('Shipping Address', max_length=60, null=True)
    city = models.CharField('City', max_length=25, null=True)
    postal_code = models.IntegerField('Postal Code', null=True)
    state = models.CharField('State', max_length=25, null=True)

    role_name = models.CharField("Role Name", max_length=25, choices=ROLE_NAME_CHOICES, default="driver", validators=[MinLengthValidator(1)])
    first_name = models.CharField("First Name", max_length=25, default="N/A", validators=[MinLengthValidator(1)])
    last_name = models.CharField("Last Name", max_length=25, default="N/A", validators=[MinLengthValidator(1)])
    phone_number = models.CharField("Phone Number", default="N/A", max_length=10)
    last_login = models.DateTimeField("Last User Login", auto_now_add=True, blank=True)
    is_email_verified = models.BooleanField("If User Verified Email", default=False)
    is_active_account = models.BooleanField("If User Has Account Enabled", default=True)
    profile_pic = models.ImageField(upload_to=upload_path,null=True, blank=True, default='/static/profile_pics/AD.png')
    sponsor = models.ForeignKey(SponsorOrganization, null=True, on_delete=models.CASCADE)
    all_sponsors = models.ManyToManyField(SponsorOrganization, related_name="all_sponsors")
    viewing_as = models.CharField("Viewing As", max_length=25, choices=ROLE_NAME_CHOICES, default="driver")
    type_to_revert_to = models.CharField("Type To Revert To", max_length=25, choices=ROLE_NAME_CHOICES, default="driver", validators=[MinLengthValidator(1)])
    approval_status = models.CharField("Approval Status", max_length=25, choices=APPROVAL_STATUS_CHOICES, default="pending")
    points_alerts = models.BooleanField("If Points Alerts Are Active", default=True)
    order_alerts = models.BooleanField("If Order Alerts Are Active", default=True)
    order_issue_alerts = models.BooleanField("If Order Issue Alerts Are Active", default=True)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'username'
    is_anonymous = False
    is_authenticated = True



    def __str__(self):
        """
        This function is used to create a string representation of the class
        Returns:
            str: user first + last name
        """
        return self.first_name + " " + self.last_name

    def check_password(self, password):
        if password == self.password:
            return True;
        else:
            return check_password(password, self.password)

class Alert(models.Model):
    receiver = models.ForeignKey(UserAccount, related_name="Receiver", null=True, on_delete=models.CASCADE)
    sender = models.ForeignKey(UserAccount, related_name="Sender", null=True, on_delete=models.CASCADE)
    message = models.CharField('Alert', max_length=250)
    timestamp = models.DateTimeField('Date/TimeAwarded', auto_now=True)
    type = models.CharField('Alert Type', max_length=15, null=True)

class Application(models.Model):
    APPROVAL_STATUS_CHOICES = (('pending','Pending'),('approved','Approved'),('denied','Denied'))

    user = models.ForeignKey(UserAccount, null=True, on_delete=models.CASCADE)
    sponsor = models.ForeignKey(SponsorOrganization, null=True, on_delete=models.CASCADE)
    status = models.CharField("Approval Status", max_length=25, choices = APPROVAL_STATUS_CHOICES, default="pending")
    points = models.IntegerField('Points', default=0)

class ApplicationAudit(models.Model):
    driver = models.ForeignKey(UserAccount, null=True, on_delete=models.CASCADE)
    sponsor = models.ForeignKey(SponsorOrganization, null=True, on_delete=models.CASCADE)
    date = models.DateTimeField('Date/TimeAwarded', auto_now=True)
    status = models.CharField("Approval Status", max_length=25)
    reason = models.CharField('Reason', max_length=250, default="N/A")

class PointsAudit(models.Model):
    awarded_to = models.CharField('Awarded To', max_length=60)
    awarded_by = models.CharField('Awarded By', max_length=60)
    num_points_awarded = models.IntegerField('Points Awarded')
    new_total = models.IntegerField('New Total', default=0)
    timestamp = models.DateTimeField('Date/Time Awarded', auto_now_add=True)
    reason = models.CharField('Reason', max_length=250, default="N/A")

class PasswordChangeAudit(models.Model):
    username = models.CharField('Username', max_length=60)
    date = models.DateTimeField('Date/Time Awarded', auto_now_add=True)
    type = models.CharField('Type of Change', max_length=25)

class LoginAudit(models.Model):
    username = models.CharField('Username', max_length=60)
    date = models.DateTimeField('Date/Time Awarded', auto_now_add=True)
    result = models.CharField('Result', max_length=25)

class Activation(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, max_length=25)

class Order(models.Model):
    """
    Model of an order a driver may create (whether pending, completed, or otherwise).
    """
    # Two-tuple for roles where item 1 is the field value, and item 2 is the display name
    ORDER_STATUS_CHOICES = (
        ('inCart', 'In-Cart'),
        ('ordered', 'Ordered'),
        ('shipping', 'Shipping'),
        ('fulfilled', 'Fulfilled'),
        ('canceled', 'Canceled'),
        ('delivered', 'Delivered'),
        ('returnRequest', 'Return In-Progress'),
        ('returned', 'Returned')
    )

    sponsor_catalog_item = models.ForeignKey("catalog.SponsorCatalogItem", on_delete=None, null=True,blank=True)
    sponsor = models.ForeignKey(SponsorOrganization, on_delete=None, null=True, blank=True)
    ordering_driver = models.ForeignKey(UserAccount, on_delete=None, null=True)
    order_status = models.CharField("Order Status", max_length=25, choices=ORDER_STATUS_CHOICES)
    last_status_change = models.DateTimeField("Last DateTime of OrderStatus Update", default=datetime.datetime.utcnow)
    retail_at_order = models.FloatField("Retail Price (MSRP) at Order Time", null=True,
                                        validators=[MinValueValidator(0.01)])
    points_at_order = models.IntegerField("Driver Point Cost at Order Time", null=True,
                                          validators=[MinValueValidator(1)])
