from django.urls import path, include
from . import views


urlpatterns = [
    path('payment_success', views.payment_success, name='payment_success'),
    path('payment_failed', views.payment_failed, name='payment_failed'),
    path('checkout', views.checkout, name='checkout'),
    path('billing_info', views.billing_info, name='billing_info'),
    path('proccess_order', views.proccess_order, name='proccess_order'),
    path('shipped_dash', views.shipped_dash, name='shipped_dash'),
    path('no_shipped_dash', views.not_shipped_dash, name='not_shipped_dash'),
    path('orders/<int:pk>', views.orders, name='orders'),
    path('paypal-ipn/', include("paypal.standard.ipn.urls")),
    path('stripe-checkout/<int:order_id>/', views.stripe_checkout, name='stripe_checkout'),
    path('izipay_checkout/<int:order_id>/', views.izipay_checkout, name='izipay_checkout'),
    path('izipay_result', views.izipay_result, name='izipay_result'),
    path('ipn', views.ipn, name='ipn'),

    path('izipay/checkout/<int:clase_id>/', views.izipay_checkout_clase, name='izipay_checkout_clase'),
    path('izipay/result/', views.izipay_result_clase, name='izipay_result_clase'),
]