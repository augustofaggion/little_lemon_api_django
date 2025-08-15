from django.contrib import admin
from .models import Category, MenuItem, CartItem, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug")
    search_fields = ("title", "slug")

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "price", "inventory", "featured")
    list_filter = ("category", "featured")
    search_fields = ("title",)

admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
