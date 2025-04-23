from django.contrib import admin
from .models import Category, Customer, Product, Order, Profile, Comment, CommentResponse
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