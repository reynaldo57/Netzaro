from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart_summary, name='cart_summary'),
    path('add/', views.cart_add, name='cart_add'),
    path('delete/', views.cart_delete, name='cart_delete'),
    path('update/', views.cart_update, name='cart_update'),
    path('apply_coupon/', views.cart_apply_coupon, name='cart_apply_coupon'),
    path('remove_coupon/', views.cart_remove_coupon, name='cart_remove_coupon'),
]