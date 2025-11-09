from django.contrib import admin
from .models import Category, Customer, Product, Order, Profile, Comment, CommentResponse, Clase
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(CommentResponse)


class UserAdmin(admin.ModelAdmin):
    model = User
    field = ["username", "first_name", "last_name", "email"]

admin.site.unregister(User)

admin.site.register(User, UserAdmin)





@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('titleClase', 'nivel', 'productClase', 'class_date', 'total_pagos')
    list_filter = ('nivel', 'class_date', 'productClase')
    search_fields = ('titleClase', 'descriptionClase')
    filter_horizontal = ('usuarios_pagados',)  # 🔥 Para gestionar usuarios que pagaron
    readonly_fields = ('class_date', 'slugClase')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('user', 'productClase', 'titleClase', 'slugClase', 'nivel')
        }),
        ('Contenido', {
            'fields': ('descriptionClase', 'fileClase', 'bannerClase')
        }),
        ('Pagos', {
            'fields': ('usuarios_pagados',)
        }),
        ('Fechas', {
            'fields': ('class_date',)
        }),
    )
    
    def total_pagos(self, obj):
        """Muestra cuántos usuarios han pagado por esta clase"""
        return obj.usuarios_pagados.count()
    total_pagos.short_description = 'Total de pagos'