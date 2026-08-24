from django.contrib import admin
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.admin import PayPalIPNAdmin as _DefaultPayPalIPNAdmin
from .models import ShippingAddress, Order, OrderItem

# Registro de modelos que no personalizamos
admin.site.register(ShippingAddress)


class OrderItemInline(admin.TabularInline):
    """Muestra qué cursos incluye cada Order directamente en su página de detalle."""
    model = OrderItem
    extra = 0
    fields = ('product', 'user', 'quantity', 'price', 'instructor_earning', 'paid_out')
    readonly_fields = ('instructor_earning',)


# Personalización de la vista del modelo Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'full_name', 'email', 'amount_paid', 'paid',
        'shipped', 'date_ordered', 'tiempo_inicio', 'tiempo_fin', 'tema_estudio'
    )
    list_filter = ('shipped', 'date_ordered')
    search_fields = ('full_name', 'email', 'tema_estudio', 'invoice', 'user__username')
    ordering = ('-date_ordered',)

    readonly_fields = ('date_ordered',)  # 👈 ¡Aquí la solución!

    inlines = [OrderItemInline]

    def get_queryset(self, request):
        # Se crea una fila de Order en cuanto el usuario hace clic en "Pagar"
        # (Izipay/PayPal la necesitan para poder buscarla luego y marcarla como
        # pagada), pero en el panel solo deben aparecer las compras ya efectuadas.
        return super().get_queryset(request).filter(paid=True)

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


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Vista de compras: quién compró, qué curso y por cuánto (PayPal e Izipay)."""
    list_display = (
        'id', 'order', 'product', 'user', 'quantity', 'price',
        'fecha_de_compra', 'paid_out',
    )
    list_filter = ('paid_out', 'product')
    search_fields = ('product__name', 'user__username', 'user__email', 'order__invoice')
    ordering = ('-order__date_ordered',)

    def get_queryset(self, request):
        # Igual que en OrderAdmin: solo mostrar cursos de órdenes ya pagadas.
        return super().get_queryset(request).filter(order__paid=True)

    def fecha_de_compra(self, obj):
        return obj.order.date_ordered if obj.order else None
    fecha_de_compra.short_description = 'Fecha de compra'


# django-paypal registra su propio admin para las notificaciones IPN, pero no
# muestra usuario, curso comprado ni monto de forma clara. Lo reemplazamos por
# una versión que cruza cada IPN con nuestra propia Order (por invoice).
admin.site.unregister(PayPalIPN)


@admin.register(PayPalIPN)
class PayPalIPNAdmin(_DefaultPayPalIPNAdmin):
    list_display = list(_DefaultPayPalIPNAdmin.list_display) + [
        'usuario_netzaro', 'cursos_comprados', 'mc_gross', 'mc_currency',
    ]

    def _order(self, obj):
        if not obj.invoice:
            return None
        if not hasattr(obj, '_netzaro_order_cache'):
            obj._netzaro_order_cache = (
                Order.objects.filter(invoice=obj.invoice)
                .select_related('user')
                .prefetch_related('orderitem_set__product')
                .first()
            )
        return obj._netzaro_order_cache

    def usuario_netzaro(self, obj):
        order = self._order(obj)
        if order and order.user:
            return order.user.username
        return (order.full_name if order else None) or obj.payer_email
    usuario_netzaro.short_description = 'Usuario'

    def cursos_comprados(self, obj):
        order = self._order(obj)
        if not order:
            return obj.item_name
        nombres = [item.product.name for item in order.orderitem_set.all() if item.product]
        return ", ".join(nombres) if nombres else obj.item_name
    cursos_comprados.short_description = 'Cursos comprados'

