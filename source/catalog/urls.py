from django.urls import path
from . import views
from accounts import urls

# URL namespace for this application.
app_name = 'catalog'

# URL patterns to be matched.
urlpatterns = [
    path('shop', views.shop, name='shop'),
    path('browse', views.browse, name = 'browse'),
    path('product-page/<int:listing_id>', views.product_page, name="product_page"),
    path('my_cart/<str:username>/<company_name>', views.my_cart, name="my_cart"),
    path('my_cart/<str:username>', views.my_cart, name="my_cart"),
    path('my_catalog', views.my_catalog, name="my_catalog"),
    path("RemoveFromCart/<int:listing_id>/<int:num>", views.RemoveFromCart, name="RemoveFromCart"),
    path('confirmPurchase/<username>/<company_name>', views.confirmPurchase, name="confirmPurchase"),
]