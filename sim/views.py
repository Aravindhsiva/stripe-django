import json
import os

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from faker import Faker

import stripe

from . import models

DOMAIN = "http://localhost:8000"  # Move this to your settings file or environment variable for production.
stripe.api_key = os.environ['STRIPE_SECRET_KEY']


def subscribe(request) -> HttpResponse:
    # We login a sample user for the demo.
    user, created = User.objects.get_or_create(
        username='Aravindhsiva', email="aravindh@increatech.com"
    )
    if created:
        user.set_password('password')
        user.save()
    login(request, user)
    request.user = user

    return render(request, 'subscribe.html')


def cancel(request) -> HttpResponse:
    return render(request, 'cancel.html')


def success(request) -> HttpResponse:

    print(f'{request.session = }')

    stripe_checkout_session_id = request.GET['session_id']

    return render(request, 'success.html')

def create_customer(request) -> HttpResponse:
    fakerInstance = Faker()
    try:
        customer = stripe.Customer.create(
         name=fakerInstance.name(),
         email=fakerInstance.safe_email()
        )

        intent =  stripe.SetupIntent.create(
            customer = customer.id,
            automatic_payment_methods={"enabled": True},
        )
        return JsonResponse(data={"customer":stripe.Customer.retrieve(id=customer.id), "secret":intent.client_secret})
    except Exception as e:
        print(e)

@csrf_exempt
def create_setup_intent(request) -> HttpResponse:
    intent =  stripe.SetupIntent.create(
        customer='cus_QgS3VjBqutfIDc',
        automatic_payment_methods={"enabled": True},
    )
    return JsonResponse(data={"secret":intent.client_secret, "id":intent.id})

def get_setup_intent(request) -> HttpResponse:
    intent =  stripe.SetupIntent.retrieve(
        id="seti_1Pp7EWIbUvrwkR54cRU6HG0s"
    )
    return JsonResponse(data=intent)

def set_default_payment_method(request)-> HttpResponse:
    customer = stripe.Customer.modify('cus_Qga3eizvKT80os',invoice_settings={'default_payment_method':"pm_1PpCuDIbUvrwkR54Mo7DOpqJ"})
    return JsonResponse(customer)

@csrf_exempt
def create_subscription(request) -> HttpResponse:
    try:
        body = json.loads(request.body.decode('utf-8'))
        price_lookup_key = body['price_lookup_key']
        customer_id = body['customer_id']
        prices = stripe.Price.list(lookup_keys=[price_lookup_key], expand=['data.product'])
        price_item = prices.data[0]
        preferred_method = stripe.Customer.retrieve(customer_id).invoice_settings.default_payment_method
        print(preferred_method)

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_item.id}],
            default_payment_method=preferred_method
        )
        return JsonResponse(subscription)
    except Exception as e:
        print(e)
        return JsonResponse(data={"error":e.args})

@csrf_exempt
def create_charge(request) -> HttpResponse:
    try:
        body = json.loads(request.body.decode('utf-8'))
        customer_id = body['customer_id']
        preferred_method = stripe.Customer.retrieve(customer_id).invoice_settings.default_payment_method
        print(preferred_method)
        charge = stripe.PaymentIntent.create(
            amount=7000,
            currency='eur',
            customer=customer_id,
            payment_method=preferred_method,
            off_session=True,
            confirm=True
        )

        # We connect the checkout session to the user who initiated the checkout.
        # models.CheckoutSessionRecord.objects.create(
        #     user=request.user,
        #     stripe_checkout_session_id=checkout_session.id,
        #     stripe_price_id=price_item.id,
        # )
        return JsonResponse(charge)
    except Exception as e:
        print(e)
        return JsonResponse(data={"error":e.args})



def create_checkout_session(request) -> HttpResponse:
    price_lookup_key = request.POST['price_lookup_key']
    try:
        prices = stripe.Price.list(lookup_keys=[price_lookup_key], expand=['data.product'])
        price_item = prices.data[0]

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {'price': price_item.id, 'quantity': 1},
                # You could add differently priced services here, e.g., standard, business, first-class.
            ],
            mode='subscription',
            customer="cus_QgF50ztItICaYM",
            success_url=DOMAIN + reverse('success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=DOMAIN + reverse('cancel')
        )

        # We connect the checkout session to the user who initiated the checkout.
        models.CheckoutSessionRecord.objects.create(
            user=request.user,
            stripe_checkout_session_id=checkout_session.id,
            stripe_price_id=price_item.id,
        )

        return redirect(
            checkout_session.url,  # Either the success or cancel url.
            code=303
        )
    except Exception as e:
        print(e)
        return HttpResponse("Server error", status=500)


def direct_to_customer_portal(request) -> HttpResponse:
    """
    Creates a customer portal for the user to manage their subscription.
    """
    checkout_record = models.CheckoutSessionRecord.objects.filter(
        user=request.user
    ).last()  # For demo purposes, we get the last checkout session record the user created.

    checkout_session = stripe.checkout.Session.retrieve(checkout_record.stripe_checkout_session_id)

    portal_session = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=DOMAIN + reverse('subscribe')  # Send the user here from the portal.
    )
    return redirect(portal_session.url, code=303)


@csrf_exempt
def collect_stripe_webhook(request) -> JsonResponse:
    """
    Stripe sends webhook events to this endpoint.
    We verify the webhook signature and updates the database record.
    """
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    signature = request.META["HTTP_STRIPE_SIGNATURE"]
    payload = request.body

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=webhook_secret
        )
    except ValueError as e:  # Invalid payload.
        raise ValueError(e)
    except stripe.error.SignatureVerificationError as e:  # Invalid signature
        raise stripe.error.SignatureVerificationError(e)

    _update_record(event)

    return JsonResponse({'status': 'success'})


def _update_record(webhook_event) -> None:
    """
    We update our database record based on the webhook event.

    Use these events to update your database records.
    You could extend this to send emails, update user records, set up different access levels, etc.
    """
    data_object = webhook_event['data']['object']
    event_type = webhook_event['type']

    if event_type == 'checkout.session.completed':
        checkout_record = models.CheckoutSessionRecord.objects.get(
            stripe_checkout_session_id=data_object['id']
        )
        checkout_record.stripe_customer_id = data_object['customer']
        checkout_record.has_access = True
        checkout_record.save()
        print('🔔 Payment succeeded!')
    elif event_type == 'customer.subscription.created':
        print('🎟️ Subscription created')
    elif event_type == 'customer.subscription.updated':
        print('✍️ Subscription updated')
    elif event_type == 'customer.subscription.deleted':
        checkout_record = models.CheckoutSessionRecord.objects.get(
            stripe_customer_id=data_object['customer']
        )
        checkout_record.has_access = False
        checkout_record.save()
        print('✋ Subscription canceled: %s', data_object.id)
    elif event_type == 'payment_method.attached':
        print("Payment Method Attached, Body : %s", data_object)
    else:
        print(f'Got an event : {event_type}')
