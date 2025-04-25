from django.contrib import admin
from .models import ShippingAddress, Order, OrderItem

# Registro de modelos que no personalizamos
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)

# Personalización de la vista del modelo Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'full_name', 'email', 'amount_paid', 'paid',
        'shipped', 'date_ordered', 'tiempo_inicio', 'tiempo_fin', 'tema_estudio'
    )
    list_filter = ('paid', 'shipped', 'date_ordered')
    search_fields = ('full_name', 'email', 'tema_estudio', 'invoice')
    ordering = ('-date_ordered',)

    readonly_fields = ('date_ordered',)  # 👈 ¡Aquí la solución!

    fieldsets = (
        ('Información del Cliente', {
            'fields': ('user', 'full_name', 'email', 'shipping_address')
        }),
        ('Detalle del Pedido', {
            'fields': ('amount_paid', 'paid', 'invoice', 'date_ordered', 'shipped', 'date_shipped')
        }),
        ('Estudio', {
            'fields': ('tiempo_inicio', 'tiempo_fin', 'tema_estudio')
        }),
    )

