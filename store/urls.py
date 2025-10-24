from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('update_password/', views.update_password, name='update_password'),
    path('update_info/', views.update_info, name='update_info'),
    path('update_user/', views.update_user, name='update_user'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:foo>', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'),
    path('search/', views.search, name='search'),
    path('add_product/', views.add_product, name='add_product'),

    path('my_products/', views.my_products, name='my_products'),
    path('update_product/<int:id>/', views.update_product, name='update_product'),
    path('user_information/<str:username>/', views.view_user_information, name='user_information'),

    path('add_clase/', views.add_clase, name='add_clase'),
    path('product/<int:id>/detail/', views.product_detail_view, name='product_detail'),
    


]