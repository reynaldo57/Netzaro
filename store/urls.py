from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import ResetPasswordRequestForm, ResetPasswordForm


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('verify_email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend_verification/', views.resend_verification_email, name='resend_verification'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
        form_class=ResetPasswordRequestForm,
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        form_class=ResetPasswordForm,
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',
    ), name='password_reset_complete'),

    path('update_password/', views.update_password, name='update_password'),
    path('update_info/', views.update_info, name='update_info'),
    path('update_user/', views.update_user, name='update_user'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:foo>', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'),
    path('search/', views.search, name='search'),
    path('add_product/', views.add_product, name='add_product'),
    path('request_teacher/', views.request_teacher, name='request_teacher'),
    path('teacher_requests/', views.teacher_requests_dash, name='teacher_requests_dash'),
    path('my_products/', views.my_products, name='my_products'),
    path('update_product/<int:id>/', views.update_product, name='update_product'),
    path('user_information/<str:username>/', views.view_user_information, name='user_information'),

    path('add_clase/', views.add_clase, name='add_clase'),
    path('product/<int:id>/detail/', views.product_detail_view, name='product_detail'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),

    path('clase/<int:clase_id>/', views.ver_clase, name='ver_clase'),
    path('clase/<int:clase_id>/completar/', views.toggle_leccion_completada, name='toggle_leccion_completada'),
    path('product/<int:product_id>/continuar/', views.continuar_curso, name='continuar_curso'),
    path('product/<int:product_id>/add_modulo/', views.add_modulo, name='add_modulo'),
    path('quiz/<int:quiz_id>/', views.tomar_quiz, name='tomar_quiz'),
    path('quiz/resultado/<int:intento_id>/', views.resultado_quiz, name='resultado_quiz'),
    path('tarea/<int:tarea_id>/', views.entregar_tarea, name='entregar_tarea'),
    path('product/<int:product_id>/entregas/', views.revisar_entregas, name='revisar_entregas'),
    path('entrega/<int:entrega_id>/calificar/', views.calificar_entrega, name='calificar_entrega'),
    path('product/<int:product_id>/certificado/', views.generar_certificado, name='generar_certificado'),
    path('certificado/verificar/<str:codigo>/', views.verificar_certificado, name='verificar_certificado'),
    path('product/<int:product_id>/add_quiz/', views.add_quiz, name='add_quiz'),
    path('quiz/<int:quiz_id>/add_pregunta/', views.add_pregunta, name='add_pregunta'),
    path('product/<int:product_id>/add_tarea/', views.add_tarea, name='add_tarea'),
    path('quiz/<int:quiz_id>/eliminar/', views.eliminar_quiz, name='eliminar_quiz'),
    path('pregunta/<int:pregunta_id>/eliminar/', views.eliminar_pregunta, name='eliminar_pregunta'),
    path('tarea/<int:tarea_id>/eliminar/', views.eliminar_tarea, name='eliminar_tarea'),
    path('instructor_dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('product/<int:product_id>/coupons/', views.manage_coupons, name='manage_coupons'),
    path('coupon/<int:coupon_id>/eliminar/', views.eliminar_coupon, name='eliminar_coupon'),
]