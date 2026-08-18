from django.shortcuts import render, redirect, get_object_or_404
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from store.models import Product, Profile, Clase, LeccionCompletada
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
    if not request.user.is_superuser:
       messages.error(request, "No tienes permiso para ver estapágina.")
       return redirect('index')
    orders = Order.objects.filter(shipped=False)
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
    orders = Order.objects.filter(shipped=True)

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

@login_required
def my_courses(request):
    product_ids = OrderItem.objects.filter(
        order__user=request.user, order__paid=True
    ).values_list('product_id', flat=True)
    products = Product.objects.filter(id__in=product_ids).distinct()

    cursos = [
        {
            'product': product,
            'porcentaje': product.porcentaje_completado(request.user),
        }
        for product in products
    ]

    actividad_reciente = LeccionCompletada.objects.filter(
        user=request.user
    ).select_related('clase', 'clase__productClase').order_by('-fecha')[:10]

    return render(request, "payment/my_courses.html", {
        "cursos": cursos,
        "actividad_reciente": actividad_reciente,
    })

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
        coupon = cart.get_coupon()
        lines, _ = _cart_lines(cart)

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

        paypal_email = settings.PAYPAL_RECEIVER_EMAIL




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
                if coupon and coupon.product_id == product.id:
                    price = coupon.precio_con_descuento(price)


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
                "coupon": coupon,
                "lines": lines,
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
                if coupon and coupon.product_id == product.id:
                    price = coupon.precio_con_descuento(price)
                #Get cuantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #Create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
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
                "order": create_order,
                "coupon": coupon,
                "lines": lines,
            })

    else:
        messages.success(request, "Access Denied")
        return redirect('index')

def _cart_lines(cart):
    coupon = cart.get_coupon()
    quantities = cart.get_quants()
    lines = []
    for product in cart.get_prods():
        base_price = product.sale_price if product.is_sale else product.price
        final_price = coupon.precio_con_descuento(base_price) if (coupon and coupon.product_id == product.id) else base_price
        qty = quantities.get(str(product.id), 1)
        lines.append({
            'product': product, 'base_price': base_price,
            'final_price': final_price, 'quantity': qty,
            'discounted': coupon is not None and coupon.product_id == product.id,
        })
    return lines, coupon

def checkout(request):
    #Get the cart
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()
    lines, coupon = _cart_lines(cart)

    if request.user.is_authenticated:
        #checkout as logged in usser
        #Shipping User
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        #Shipping Form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form, "coupon": coupon, "lines": lines})
    else:
        #checkout as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form, "coupon": coupon, "lines": lines})

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
    auth = 'Basic ' + base64.b64encode(f"{keys['USERNAME']}:{keys['PASSWORD']}".encode('utf-8')).decode('utf-8')

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


@login_required
def comprar_curso_izipay(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    price = product.precio_acceso_completo()

    order = Order.objects.create(
        user=request.user,
        full_name=request.user.get_full_name() or request.user.username,
        email=request.user.email,
        shipping_address="",
        amount_paid=price,
    )
    OrderItem.objects.create(
        order=order, product=product, user=request.user, quantity=1, price=price,
    )
    return izipay_checkout(request, order.id)



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

    order_id = answer_json["orderDetails"]["orderId"]
    order = Order.objects.get(id=order_id)
    if answer_json.get("orderStatus") == "PAID":
        order.paid = True
        order.save()

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

    order = Order.objects.get(id=orderId)
    if orderStatus == "PAID":
        order.paid = True
        order.save()

    return HttpResponse(status=200, content=f"OK! OrderStatus is {orderStatus} ")

def checkHash(response, key):

    answer = response['kr-answer'].encode('utf-8')

    calculateHash = hmac.new(key.encode('utf-8'), answer, hashlib.sha256).hexdigest()

    return calculateHash == response['kr-hash']






def izipay_checkout_clase(request, clase_id):
    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'
    clase = get_object_or_404(Clase, id=clase_id)

    auth = 'Basic ' + base64.b64encode(f"{keys['USERNAME']}:{keys['PASSWORD']}".encode('utf-8')).decode('utf-8')
    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    # URL absoluta para que Izipay POSTee y redirija
    result_url = request.build_absolute_uri(reverse('izipay_result_clase'))
    
    data = {
        "amount": 200, #aqui cambias la cantidad de dinero que quieres cobrar
        "currency": "USD",
        "orderId": f"CLASE-{clase.id}",
        "customer": {
            "email": request.user.email if request.user.is_authenticated else "anonimo@example.com",
            "reference": str(clase.id),
        },
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    if response.status_code != 200 or response_data.get('status') != 'SUCCESS':
        return HttpResponse(f"Error en la respuesta de Izipay: {response_data}", status=500)

    token = response_data['answer']['formToken']

    return render(request, 'checkout_izipay_clase.html', {
        'token': token,
        'publickey': keys['PUBLIC_KEY'],
        'clase': clase,
        'result_url': result_url,
    })

@csrf_exempt
def izipay_result_clase(request):
    # Manejar redirección GET
    if request.method == 'GET':
        messages.info(request, "Por favor completa el pago para descargar el PDF.")
        return redirect('home')
    
    # Manejar POST (respuesta de Izipay)
    if not request.POST:
        return HttpResponse("No post data received!", status=400)

    if not checkHash(request.POST, keys["HMACSHA256"]):
        return HttpResponse("Firma inválida", status=403)

    answer_json = json.loads(request.POST['kr-answer'])
    order_id = answer_json["orderDetails"]["orderId"]
    
    # Verificar que sea una orden de clase
    if not order_id.startswith("CLASE-"):
        return HttpResponse("Orden inválida", status=400)
    
    clase_id = order_id.split("-")[1]
    clase = get_object_or_404(Clase, id=clase_id)
    product_id = clase.productClase.id

    # 🔥 Marcar clase como pagada si el pago fue exitoso
    if answer_json.get("orderStatus") == "PAID":
        if request.user.is_authenticated:
            # Marcar clase como pagada para este usuario
            clase.marcar_como_pagada(request.user)
            messages.success(request, f"✅ Pago exitoso. Ahora puedes descargar el PDF de '{clase.titleClase}'.")
        else:
            # Si el usuario no está autenticado, guardar en sesión temporalmente
            clases_pagadas = request.session.get('clases_pagadas', [])
            if clase_id not in clases_pagadas:
                clases_pagadas.append(clase_id)
                request.session['clases_pagadas'] = clases_pagadas
                request.session.modified = True
            messages.warning(request, "⚠️ Inicia sesión para mantener tu compra permanentemente.")
    else:
        messages.error(request, "⚠️ El pago no se completó. Por favor, inténtalo nuevamente.")

    return redirect('product_detail', id=product_id)

def checkHash(response, key):
    """Verifica la firma del mensaje (seguridad Izipay)"""
    answer = response['kr-answer'].encode('utf-8')
    calculateHash = hmac.new(key.encode('utf-8'), answer, hashlib.sha256).hexdigest()
    return calculateHash == response['kr-hash']

@login_required
def comprar_curso_paypal(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    price = product.precio_acceso_completo()

    paypal_email = settings.PAYPAL_RECEIVER_EMAIL

    my_Invoice = str(uuid.uuid4())

    order = Order.objects.create(
        user=request.user,
        full_name=request.user.get_full_name() or request.user.username,
        email=request.user.email,
        shipping_address="",
        amount_paid=price,
        invoice=my_Invoice,  # necesario: el IPN de PayPal busca la orden por este campo
    )
    OrderItem.objects.create(
        order=order, product=product, user=request.user, quantity=1, price=price,
    )

    host = request.get_host()
    paypal_dict = {
        'business': paypal_email,
        'amount': price,
        'item_name': product.name,
        'no_shipping': '2',
        'invoice': my_Invoice,
        'currency_code': 'USD',
        'notify_url': 'https://{}{}'.format(host, reverse("paypal-ipn")),
        'return_url': 'https://{}{}'.format(host, reverse("payment_success")),
        'cancel_return': 'https://{}{}'.format(host, reverse("payment_failed")),
    }
    paypal_form = PayPalPaymentsForm(initial=paypal_dict)

    return render(request, 'payment/comprar_curso_paypal.html', {
        'paypal_form': paypal_form, 'product': product, 'price': price,
    })

@login_required
def platform_commission_dash(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para ver esta página.")
        return redirect('index')

    from django.db.models import Sum
    items = OrderItem.objects.filter(order__paid=True)
    total_recaudado = items.aggregate(s=Sum('price'))['s'] or 0
    total_comision = items.aggregate(s=Sum('platform_commission'))['s'] or 0
    total_pendiente = items.filter(paid_out=False).aggregate(s=Sum('instructor_earning'))['s'] or 0

    por_profesor = items.filter(paid_out=False).values('product__user__username').annotate(
        pendiente=Sum('instructor_earning'),
    ).order_by('-pendiente')

    return render(request, 'payment/platform_commission_dash.html', {
        'total_recaudado': total_recaudado,
        'total_comision': total_comision,
        'total_pendiente': total_pendiente,
        'por_profesor': por_profesor,
    })


@login_required
def generar_planilla_pago(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para ver esta página.")
        return redirect('index')

    from django.db.models import Sum

    items_pendientes = OrderItem.objects.filter(order__paid=True, paid_out=False)

    resumen = items_pendientes.values(
        'product__user__id', 'product__user__username',
        'product__user__first_name', 'product__user__last_name',
        'product__user__profile__yape_plin_number',
    ).annotate(monto=Sum('instructor_earning')).order_by('-monto')

    if request.method == 'POST':
        return _descargar_planilla_yape_plin(items_pendientes)

    return render(request, 'payment/generar_planilla_pago.html', {'resumen': resumen})

def _descargar_planilla_yape_plin(items_pendientes):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from django.http import HttpResponse
    from django.utils import timezone

    por_profesor = {}
    for item in items_pendientes.select_related('product__user__profile'):
        profesor = item.product.user
        if profesor.id not in por_profesor:
            por_profesor[profesor.id] = {
                'nombre': profesor.get_full_name() or profesor.username,
                'celular': getattr(profesor.profile, 'yape_plin_number', ''),
                'monto': 0,
                'item_ids': [],
            }
        por_profesor[profesor.id]['monto'] += item.instructor_earning
        por_profesor[profesor.id]['item_ids'].append(item.id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Pago Yape-Plin"
    ws.append(["Profesor", "Celular (Yape/Plin)", "Monto a pagar (S/.)", "Glosa"])
    for cell in ws[1]:
        cell.font = Font(bold=True)

    ids_incluidos = []
    for data in por_profesor.values():
        ws.append([
            data['nombre'],
            data['celular'] or "SIN NÚMERO REGISTRADO",
            float(data['monto']),
            "Pago Netzaro - cursos vendidos",
        ])
        ids_incluidos.extend(data['item_ids'])

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 30

    OrderItem.objects.filter(id__in=ids_incluidos).update(
        paid_out=True, paid_out_date=timezone.now()
    )

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"planilla_pago_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response