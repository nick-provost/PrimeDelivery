from django.shortcuts import render
from django.conf import settings
from accounts.models import *
from catalog.models import CatalogItem, SponsorCatalogItem, CatalogItemImage, ItemReview
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import generics
from django.utils import timezone
from.forms import *
import json
import requests 
from etsy2 import Etsy
from django.contrib import messages

base_url = settings.ETSY_BASE_URL
key = settings.ETSY_API_KEY

# Driver view
def shop(request):      
    user = UserAccount.objects.get(username=request.user.username)
    company = user.sponsor
    listings = SponsorCatalogItem.objects.filter(sponsor_company=company)
    images = CatalogItemImage.objects.all()
    return render(request, "accounts/catalog/shop.html", {'listings': listings, 'images': images})

# Sponsor view for adding items to catalog
def browse(request):
    company_to_add_to = request.user.sponsor.company_name
    
    etsy = Etsy(api_key=key)
    listings = etsy.findAllListingActive()
    for item in listings:
        this_id = item['listing_id']
        if not CatalogItem.objects.filter(listing_id=this_id).exists():
            url = base_url + '/listings/{}?includes=Images&api_key={}'.format(item['listing_id'], key)
            response = requests.request("GET", url)
            search_was_successful = (response.status_code == 200)
            data = response.json()
            listing_data = data['results'][0]

            listing = CatalogItem.objects.create(listing_id=item['listing_id'])
            
            listing.last_updated = timezone.now()
            listing.last_modified = item['last_modified_tsz']
            # check if the modfied time has been changed
            if item['title']: 
                this_title = item['title']
                listing.item_name = this_title
            if item['description']:
                this_description = item['description']
                listing.item_description = this_description
            # ignore foreign currency for now
            if item['price']:
                this_price = item['price']
                listing.retail_price = float(this_price)
            if item['state'] == "active":
                listing.is_available = True
            else:
                listing.is_available = False
            listing.save()

            images = etsy.findAllListingImages(listing_id=this_id)
            for image in images:
                img = CatalogItemImage.objects.create(catalog_item = listing, image_link = image['url_170x135'], big_image_link = image['url_570xN'] )
                img.save()
    temp = {}
    for it, (k,v) in enumerate(request.POST.items()):
        temp[k] = v
    form = AddToCatalogForm(temp)
    if request.method == 'POST' and form.is_valid():
        new_item = CatalogItem.objects.get(listing_id=temp['catalog_item'])
        cost = new_item.retail_price
        new_catalog_item = SponsorCatalogItem(catalog_item=new_item, sponsor_company=request.user.sponsor, point_value=cost, is_available_to_drivers=True)
        new_catalog_item.save()
        messages.success(request, 'Item Successfully Added To Your Catalog')
    
        imgs = CatalogItemImage.objects.all()
        return render(request, "accounts/catalog/browse.html", {'listings': listings, 'imgs':imgs})
    else:
        form = AddToCatalogForm()
        imgs = CatalogItemImage.objects.all()
        return render(request, "accounts/catalog/browse.html", {'listings': listings, 'imgs':imgs})


def product_page(request, listing_id):
    company = request.user.sponsor
    tempItem = CatalogItem.objects.get(listing_id=listing_id)
    itemPrice = float(tempItem.retail_price)
    item = SponsorCatalogItem.objects.get(catalog_item=tempItem)
    sponsor_ratio = item.sponsor_company.point_ratio
    cost_in_points = (sponsor_ratio*100)*itemPrice
    point_value = int(cost_in_points)
    item.point_value = point_value
    item.save()
    images = CatalogItemImage.objects.all()
    form = AddToCatalogForm()
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            this_driver = UserAccount.objects.get(username=request.user.username)
            if CartItem.objects.filter(item=item, driver=this_driver).exists():
                updateCartItem = CartItem.objects.get(item=item, driver=this_driver)
                tempQty = updateCartItem.quantity
                updateCartItem.quantity = tempQty + 1
                updateCartItem.save()
            else:
                newCartItem = CartItem(item=item, driver=this_driver, quantity=1)
                newCartItem.save()
            messages.success(request, 'Item Successfully Added To Your Cart')

    return render(request, "accounts/catalog/product_page.html", {'listing_id': listing_id, 'item': item, 'images': images, 'itemPrice': itemPrice, 'point_value': point_value})


def my_cart(request, username, company_name):
    this_driver = UserAccount.objects.get(username=request.user.username)
    this_sponsor = SponsorOrganization.objects.get(company_name=company_name)
    catalog_items_this_sponsor = SponsorCatalogItem.objects.filter(sponsor_company=this_sponsor)
    cart_items_this_driver = CartItem.objects.filter(driver=this_driver)
    cart_items_this_sponsor = CartItem.objects.none()
    for item in cart_items_this_driver:
        for sponsor_item in catalog_items_this_sponsor:
            if item.item == sponsor_item:
                current_item = CartItem.objects.filter(item=sponsor_item)
                cart_items_this_sponsor |= current_item
    images = CatalogItemImage.objects.all()
    total = 0
    for item in cart_items_this_sponsor:
        qty = item.quantity
        price_each = item.item.point_value
        temp = int(qty*price_each)
        item.total_cost = temp
        item.save()
        total = total + temp
    form = RemoveFromCartForm()
    return render(request, "accounts/catalog/my_cart.html", {'driver':this_driver, 'items':cart_items_this_sponsor, 'images':images, 'total': total, 'form':form})

def RemoveFromCart(request, listing_id, num):
    this_driver = UserAccount.objects.get(username=request.user.username)
    cart_items = CartItem.objects.filter(driver=this_driver)
    images = CatalogItemImage.objects.all()
    item = CatalogItem.objects.get(listing_id=listing_id)
    sponsor_item = SponsorCatalogItem.objects.get(catalog_item=item, sponsor_company=this_driver.sponsor)
    item_to_remove=CartItem.objects.get(item_id=sponsor_item.id, driver_id=this_driver.id)
    if num == 1:
        if item_to_remove.quantity==1:
            item_to_remove.delete()
            messages.success(request, 'Item Successfully Removed From Your Cart')
        else:
            qty = item_to_remove.quantity-1
            item_to_remove.quantity = qty
            item_to_remove.save()
            messages.success(request, '1x Item Successfully Removed From Your Cart')
    else:
        item_to_remove.delete()
        messages.success(request, 'Item Successfully Removed From Your Cart')
    total = 0
    for item in cart_items:
        qty = item.quantity
        price_each = item.item.point_value
        temp = int(qty*price_each)
        item.total_cost = temp
        item.save()
        total = total + temp

    form = RemoveFromCartForm()
    return render(request, "accounts/catalog/my_cart.html", {'driver':this_driver, 'items':cart_items, 'images':images, 'total':total, 'form':form})


def my_catalog(request):
    if request.user.role_name == "sponsor":
        user = UserAccount.objects.get(username=request.user.username)
        company = user.sponsor
        items = SponsorCatalogItem.objects.filter(sponsor_company=company)
        images = CatalogItemImage.objects.all()

        form = AddToCatalogForm(request.POST)
        if request.method == "POST":
            item = request.POST['catalog_item']
            start = item.find("(") + len("(")
            end = item.find(")")
            sub = item[start:end]
            item_to_delete = SponsorCatalogItem.objects.get(id=sub)
            item_to_delete.delete()
            messages.success(request, 'Item Successfully Removed From Your Catalog')

        form = DeleteFromCatalogForm()
        return render(request, "accounts/catalog/my_catalog.html", context = {'items': items, 'images': images, 'form':form}) 

    else:
        form = ViewCatalogAsAdminForm(request.POST)
        images = CatalogItemImage.objects.all()
        items = SponsorCatalogItem.objects.none()
        if request.GET.get('sponsor'):
            company = SponsorOrganization.objects.get(id=request.GET.get('sponsor'))
            items = SponsorCatalogItem.objects.filter(sponsor_company=company)
        form = AddToCatalogForm(request.POST)
        if request.method == "POST":
            item = request.POST['catalog_item']
            start = item.find("(") + len("(")
            end = item.find(")")
            sub = item[start:end]
            item_to_delete = SponsorCatalogItem.objects.get(id=sub)
            item_to_delete.delete()
            messages.success(request, 'Item Successfully Removed From Your Catalog')

        form = ViewCatalogAsAdminForm()
        return render(request, "accounts/catalog/my_catalog.html", context = {'form':form, 'items':items, 'images':images})

def confirmPurchase(request, username, company_name):
    this_driver = UserAccount.objects.get(username=request.user.username)
    this_sponsor = SponsorOrganization.objects.get(company_name=company_name)
    catalog_items_this_sponsor = SponsorCatalogItem.objects.filter(sponsor_company=this_sponsor)
    cart_items_this_driver = CartItem.objects.filter(driver=this_driver)
    cart_items_this_sponsor = CartItem.objects.none()
    for item in cart_items_this_driver:
        for sponsor_item in catalog_items_this_sponsor:
            if item.item == sponsor_item:
                current_item = CartItem.objects.filter(item=sponsor_item)
                cart_items_this_sponsor |= current_item
    images = CatalogItemImage.objects.all()
    total = 0
    count = 0
    for item in cart_items_this_sponsor:
        qty = item.quantity
        price_each = item.item.point_value
        temp = int(qty*price_each)
        item.total_cost = temp
        item.save()
        total = total + temp
        count = count + 1

    this_app = Application.objects.get(user=this_driver, sponsor=this_sponsor, status="approved")
    driver_points = this_app.points
    if driver_points >= total:
        this_order_alert = Alert.objects.create()
        this_order_alert.receiver = this_driver
        this_order_alert.sender = UserAccount.objects.filter(sponsor=this_sponsor)[0]
        this_order_alert.message = "You have placed an order with " + this_sponsor.company_name + " for " + str(count) + " items totaling " + str(total) + " points."
        this_order_alert.type = "order"
        this_order_alert.save()
        this_app.points = this_app.points - total
        this_driver.num_of_points = this_driver.num_of_points - total
        this_app.save()
        this_driver.save()
        for item in cart_items_this_sponsor:
            listing_id = item.item.catalog_item.listing_id
            quantity = item.quantity
            this_catalog_item = CatalogItem.objects.get(listing_id=listing_id)
            this_sponsor_catalog_item = item.item
            this_order = Order.objects.create()
            this_order.sponsor_catalog_item = this_sponsor_catalog_item
            this_order.sponsor = this_sponsor
            this_order.ordering_driver = this_driver
            this_order.order_status = "Ordered"
            this_order.retail_at_order = this_catalog_item.retail_price
            this_order.points_at_order = this_catalog_item.retail_price*100
            this_order.save()

            RemoveFromCart(request, listing_id, quantity)
            
    else:
        messages.error(request, 'ERROR: You do not have enough points for this order!')
    form = RemoveFromCartForm()
    return render(request, "accounts/catalog/my_cart.html", {'driver':this_driver, 'items':cart_items_this_driver, 'images':images, 'total':total, 'form':form})

