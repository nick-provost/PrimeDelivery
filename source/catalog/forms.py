from django import forms
from .models import *

class AddToCatalogForm(forms.Form):
    class Meta:
        model = SponsorCatalogItem
        fields = ['catalog_item']

class AddToCartForm(forms.Form):
    class Meta:
        model = SponsorCatalogItem
        fields = ['catalog_item']
    
class DeleteFromCatalogForm(forms.Form):
    class Meta:
        model = SponsorCatalogItem
        fields = ['catalog_item']

class RemoveFromCartForm(forms.Form):
    class Meta:
        model = CartItem
        fields = ['item']

class ViewCatalogAsAdminForm(forms.Form):
    class Meta:
        model = SponsorOrganization
        fields = ['sponsor']
 
    sponsor = forms.ModelChoiceField(queryset=SponsorOrganization.objects.all())
