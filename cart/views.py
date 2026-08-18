from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from store.models import Product
from django.http import JsonResponse
from django.contrib import messages

# Create your views here.

def cart_summary(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()
    coupon = cart.get_coupon()
    return render(request, "cart_summary.html", {"cart_products":cart_products, "quantities": quantities, "totals": totals, "coupon": coupon,})

def cart_apply_coupon(request):
    cart = Cart(request)
    if request.method == 'POST':
        coupon = cart.apply_coupon(request.POST.get('coupon_code'))
        if coupon:
            messages.success(request, f'Cupón "{coupon.code}" aplicado: -{coupon.discount_percent}% en "{coupon.product.name}"')
        else:
            messages.error(request, "Cupón inválido, vencido o agotado")
    return redirect('cart_summary')


def cart_remove_coupon(request):
    cart = Cart(request)
    cart.remove_coupon()
    messages.success(request, "Cupón removido")
    return redirect('cart_summary')

def cart_add(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        product = get_object_or_404(Product, id=product_id)

        cart.add(product=product, quantity=product_qty)

        cart_quantity = cart.__len__()

        #response = JsonResponse({'Procuct Name: ': product.name})
        response = JsonResponse({'qty': cart_quantity})
        messages.success(request, ("Product added to cart"))
        return response


def cart_delete(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        cart.delete(product=product_id)

        response = JsonResponse({'product':product_id})
        messages.success(request, ("Item deleted"))
        return response

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        cart.update(product=product_id, quantity=product_qty)

        response = JsonResponse({'qty':product_qty})
        messages.success(request, ("Your cart was been updated"))
        return response

