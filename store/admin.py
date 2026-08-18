from django.contrib import admin
from .models import (
    Category, Customer, Product, Order, Profile, Comment, CommentResponse, Clase,
    Quiz, Pregunta, Opcion, IntentoQuiz, Tarea, EntregaTarea, Certificado, Coupon,
)
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

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'quiz')
    inlines = [OpcionInline]


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'product', 'nota_minima_aprobatoria')
    list_filter = ('product',)
    inlines = [PreguntaInline]


@admin.register(IntentoQuiz)
class IntentoQuizAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'puntaje', 'aprobado', 'fecha')
    list_filter = ('aprobado', 'quiz')


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'product', 'fecha_limite')
    list_filter = ('product',)


@admin.register(EntregaTarea)
class EntregaTareaAdmin(admin.ModelAdmin):
    list_display = ('user', 'tarea', 'estado', 'fecha_entrega')
    list_filter = ('estado', 'tarea')


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'user', 'product', 'fecha_emision')
    readonly_fields = ('codigo', 'fecha_emision')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'product', 'discount_percent', 'active', 'times_used', 'valid_until')
    list_filter = ('active', 'product')
    search_fields = ('code',)