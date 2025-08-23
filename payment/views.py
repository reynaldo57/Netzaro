from django.shortcuts import render, redirect
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from store.models import Product, Profile
import datetime
#import some paypal stuff
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid #unique user id for duplicated orders

from django.utils import timezone

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from django.contrib.auth.decorators import login_required
import stripe

# Create your views here.



def orders(request, pk):
    if request.user.is_authenticated and request.user.is_authenticated:
        #Get the Order
        order = Order.objects.get(id=pk)
        #Get the order items
        items = OrderItem.objects.filter(order=pk)

        if request.POST:
            status = request.POST['shipping_status']
            #Check if true or false
            if status == "true":
                #Get the order
                order = Order.objects.filter(id=pk)
                #Update the status
                now = timezone.now()
                order.update(shipped=True, date_shipped = now)
            else:
                #Get the order
                order = Order.objects.filter(id=pk)
                #Update the status
                order.update(shipped=False)
            messages.success(request, "Shipping Status Updated")
            return redirect('index')
            
        return render(request, 'payment/orders.html',{"order":order, "items":items})
    else:
        messages.success(request, "Order Placed")
        return redirect('index')

@login_required
def not_shipped_dash(request):
    orders = Order.objects.filter(user=request.user, shipped=False)
    if request.method == "POST":
        status = request.POST.get('shipping_status')
        num = request.POST.get('num')

        try:
            # Buscar sólo entre las órdenes del usuario
            order = Order.objects.get(id=num, user=request.user)
            #Grab Date and time
            now = timezone.now()

            order.shipped = True

            order.date_shipped = now
            order.save()

            #redirect
            messages.success(request, "Shipping Status Updated")
        except Order.DoesNotExist:
            messages.error(request, "Order not found or you do not have permission.")
        return redirect('not_shipped_dash')  # Puedes redirigir de nuevo a este dashboard

    return render(request, "payment/not_shipped_dash.html", {"orders": orders})

@login_required
def shipped_dash(request):
    # Mostrar sólo las órdenes YA enviadas del usuario autenticado
    orders = Order.objects.filter(user=request.user, shipped=True)

    if request.method == "POST":
        status = request.POST.get('shipping_status')
        num = request.POST.get('num')

        try:
            # Buscar sólo entre las órdenes del usuario
            order = Order.objects.get(id=num, user=request.user)

            order.shipped = False
            order.save()

            messages.success(request, "Shipping Status Updated")
        except Order.DoesNotExist:
            messages.error(request, "Order not found or you do not have permission.")

        return redirect('shipped_dash')  # Puedes redirigir de nuevo a este dashboard

    return render(request, "payment/shipped_dash.html", {"orders": orders})

def proccess_order(request):
    if request.POST:
        #Get the cart
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        # Get Billing Info from the last Page
        payment_form = PaymentForm(request.POST or None)
        #Get shipping Session Data
        my_shipping = request.session.get('my_shipping')
        #Gather Order Info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        #Create Shipping Address from session info
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals

        #Create an order
        if request.user.is_authenticated:
            #logged in
            user = request.user
            #Create Order
            create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            #Add order items

            # Get the order ID
            order_id = create_order.pk

            #Get product Info
            for product in cart_products():
                #get Product ID
                product_id = product.id
                #get Product Price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get cuantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #Create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
                        create_order_item.save()
            # Delete our cart
            for key in list(request.session.keys()):
                if key == "session_key":
                    #Delete the key
                    del request.session[key]

            #Delete Cart from Database (old_cart field)
            current_user = Profile.objects.filter(user__id=request.user.id)
            #delete shoppin cart in database (old_cart field)
            current_user.update(old_cart="")


            messages.success(request, "Order Placed")
            return redirect('index')
        else:
            #not logged in
            #Create Order
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            #Add order items
            
            # Get the order ID
            order_id = create_order.pk

            #Get product Info
            for product in cart_products():
                #get Product ID
                product_id = product.id
                #get Product Price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get cuantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #Create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, quantity=value, price=price)
                        create_order_item.save()

            # Delete our cart
            for key in list(request.session.keys()):
                if key == "session_key":
                    #Delete the key
                    del request.session[key]

            messages.success(request, "Order Placed")
            return redirect('index')

    else:
        messages.success(request, "Access Denied")
        return redirect('index')

def billing_info(request):
    # Detectar si el usuario hizo clic en "Pagar con tarjeta"
    if request.POST:
        metodo_pago = request.POST.get("pago_metodo", "paypal")
        #Get the cart
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        #Create a session with Shipping Info
        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping

        #Gather Order Info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']

        # Recoger nuevos campos
        tiempo_inicio = my_shipping.get('shipping_tiempo_inicio')
        tiempo_fin = my_shipping.get('shipping_tiempo_fin')
        tema_estudio = my_shipping.get('shipping_tema_estudio')
        
        try:
            tiempo_inicio = make_aware(parse_datetime(tiempo_inicio)) if tiempo_inicio else None
        except Exception:
            tiempo_inicio = None

        try:
            tiempo_fin = make_aware(parse_datetime(tiempo_fin)) if tiempo_fin else None
        except Exception:
            tiempo_fin = None

        #Create Shipping Address from session info
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals


        #Get the host
        host = request.get_host()

        #Create Invoice Number
        my_Invoice = str(uuid.uuid4())




        # Validar que todos los productos sean del mismo dueño
        product_list = cart_products()
        if not product_list:
            messages.error(request, "No hay cursos reservados")
            return redirect('cart_summary')  # o cualquier vista segura
        owners = set(p.user for p in product_list)
        if len(owners) > 1:
            messages.error(request, "No puedes pagar productos de diferentes vendedores en un solo pago.")
            return redirect('cart_summary')

        # Obtener correo PayPal del dueño del producto
        first_product = product_list[0]
        user = first_product.user
        try:
            profile = Profile.objects.get(user=user)
            paypal_email = profile.paypal_email
        except Profile.DoesNotExist:
            paypal_email = None

        if not paypal_email:
            paypal_email = settings.PAYPAL_RECEIVER_EMAIL  # fallback




        #Create Paypal Form Dictionary
        paypal_dict = {
            'business': paypal_email,
            'amount': totals,
            'item_name': 'Book Order',
            'no_shipping': '2',
            'invoice': my_Invoice,
            'currency_code': 'USD', #EUROS FOR EUROS
            'notify_url': 'https://{}{}'.format(host, reverse("paypal-ipn")),
            'return_url': 'https://{}{}'.format(host, reverse("payment_success")),
            'cancel_return': 'https://{}{}'.format(host, reverse("payment_failed")),
        }
        #Create acutal paypal button
        paypal_form = PayPalPaymentsForm(initial=paypal_dict)



        #Check to see if user is logged in
        if request.user.is_authenticated:
            #get the billing form
            billing_form = PaymentForm()



            #logged in
            user = request.user
            #Create Order
            create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid, invoice=my_Invoice, tiempo_inicio=tiempo_inicio, tiempo_fin=tiempo_fin, tema_estudio=tema_estudio)
            create_order.save()

            #Add order items

            # Get the order ID
            order_id = create_order.pk

            #Get product Info
            for product in cart_products():
                #get Product ID
                product_id = product.id
                #get Product Price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get cuantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #Create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
                        create_order_item.save()
            # Delete our cart
            for key in list(request.session.keys()):
                if key == "session_key":
                    #Delete the key
                    del request.session[key]

            #Delete Cart from Database (old_cart field)
            current_user = Profile.objects.filter(user__id=request.user.id)
            #delete shoppin cart in database (old_cart field)
            current_user.update(old_cart="")

            return render(request, "payment/billing_info.html", {
                "paypal_form":paypal_form, 
                "cart_products":cart_products, 
                "quantities": quantities, 
                "totals": totals, 
                "shipping_info": request.POST, 
                "billing_form": billing_form,
                "metodo_pago": metodo_pago,       # <-- NUEVO
                "order": create_order,
                })

        else:
            #not logged in
            #Create Order
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid, invoice=my_Invoice, tiempo_inicio=tiempo_inicio, tiempo_fin=tiempo_fin, tema_estudio=tema_estudio)
            create_order.save()

            #Add order items

            # Get the order ID
            order_id = create_order.pk

            #Get product Info
            for product in cart_products():
                #get Product ID
                product_id = product.id
                #get Product Price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get cuantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #Create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, quantity=value, price=price)
                        create_order_item.save()

            #NOt logged In
            #get the billing form
            billing_form = PaymentForm()
            return render(request, "payment/billing_info.html", {
                "paypal_form":paypal_form, 
                "cart_products":cart_products, 
                "quantities": quantities, 
                "totals": totals, 
                "shipping_info": request.POST, 
                "billing_form": billing_form,
                "metodo_pago": metodo_pago,       # <-- NUEVO
                "order": create_order  
            })

    else:
        messages.success(request, "Access Denied")
        return redirect('index')

def checkout(request):
    #Get the cart
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    if request.user.is_authenticated:
        #checkout as logged in usser
        #Shipping User
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        #Shipping Form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})
    else:
        #checkout as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})


def payment_success(request):
    #Delete the browse cart
    #First GET the cart
    #First Get the cart
    #Get the cart
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    #Delete our cart
    for key in list(request.session.keys()):
        if key == "session_key":
            #Delete the key
            del request.session[key]
    return render(request, "payment/payment_success.html")

def payment_failed(request):
    return render(request, "payment/payment_failed.html")





stripe.api_key = 'sk_test_51RNf7xQvKPW9lI3d6Ywv4jvGemcWfClXw6OPja1i9pZh7eq2qRf9SCivF9fEkQpQ9lXCRteZids2EXno3vwLT4hq00mkjIudgO'

def stripe_checkout(request, order_id):
    order = Order.objects.get(id=order_id)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Pedido #{order.invoice}",
                },
                'unit_amount': int(order.amount_paid * 100),  # en centavos
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success')),
        cancel_url=request.build_absolute_uri(reverse('payment_failed')),
    )

    return redirect(session.url, code=303)






from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import base64
import json
import requests
import hashlib
import hmac
from django.http import HttpResponse
from Keys.keys import keys


def izipay_checkout(request, order_id):
    #URL de Web Service REST
    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'
    order = Order.objects.get(id=order_id)
    

    #Encabezado Basic con concatenación de "usuario:contraseña" en base64
    auth = 'Basic ' + base64.b64encode(f"{keys["USERNAME"]}:{keys["PASSWORD"]}".encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
    }

    data = {
        "amount": int(order.amount_paid * 100),  # en centavos
        "currency": 'USD',
        "orderId": str(order_id),
        
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response.status_code != 200 or response_data.get('status') != 'SUCCESS':
        return HttpResponse(f"Error en la respuesta de Izipay: {response_data}", status=500)

    token = response_data['answer']['formToken']

    
    token = response_data['answer']['formToken']
    print(token)
    return render(request, 'checkout_izipay.html', {'token': token, 'publickey': keys['PUBLIC_KEY']})

@csrf_exempt
def izipay_result(request):
    if not request.POST: 
        raise Exception("No post data received!")

    #Validación de firma
    if not checkHash(request.POST, keys["HMACSHA256"]) : 
        raise Exception("Invalid signature")

    answer_json = json.loads(request.POST['kr-answer'])
    krAnswerData = json.dumps(answer_json, indent=2)
    postData = json.dumps(request.POST, indent=4)

    answer_json["orderDetails"]["orderTotalAmount"] = answer_json["orderDetails"]["orderTotalAmount"] / 100

    return render(request, 'izipay_result.html', {'answer': answer_json, 'postData': postData, 'krAnswerData': krAnswerData})

@csrf_exempt
def ipn(request):
    if not request.POST: 
        raise Exception("No post data received!")

    #Validación de firma en IPN
    if not checkHash(request.POST, keys["PASSWORD"]) : 
        raise Exception("Invalid signature")
    
    answer = json.loads(request.POST['kr-answer']) 
    transaction = answer['transactions'][0]

    #Verificar orderStatus: PAID / UNPAID
    orderStatus = answer['orderStatus']
    orderId = answer['orderDetails']['orderId']
    transactionUuid = transaction['uuid']

    return HttpResponse(status=200, content=f"OK! OrderStatus is {orderStatus} ")

def checkHash(response, key):

    answer = response['kr-answer'].encode('utf-8')

    calculateHash = hmac.new(key.encode('utf-8'), answer, hashlib.sha256).hexdigest()

    return calculateHash == response['kr-hash']