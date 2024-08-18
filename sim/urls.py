from django.contrib import admin
from django.urls import include, path

from sim import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('cancel/', views.cancel, name='cancel'),
    path('success/', views.success, name='success'),
    path('create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    path('create-subscription/', views.create_subscription, name='create-subscription'),
    path('create-charge/', views.create_charge, name='create_charge'),
    path('direct-to-customer-portal/', views.direct_to_customer_portal, name='direct-to-customer-portal'),
    path('collect-stripe-webhook/', views.collect_stripe_webhook, name='collect-stripe-webhook'),
    path('create-customer/', views.create_customer, name='create-customer'),
    path('create-setup-intent/', views.create_setup_intent, name='create-setup-intent'),
    path('update-default-method/', views.set_default_payment_method, name='update-default-method'),
    path('get-setup-intent/', views.get_setup_intent, name='get-setup-intent'),
]
