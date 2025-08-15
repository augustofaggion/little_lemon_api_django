from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, CartItem, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "slug"]

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "inventory", "featured", "category", "category_id"]

class CartItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(
        source="menuitem", queryset=MenuItem.objects.all(), write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "menuitem", "menuitem_id", "quantity", "unit_price", "price"]

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "quantity", "unit_price", "price"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.PrimaryKeyRelatedField(
        source="delivery_crew", queryset=User.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "delivery_crew_id", "status", "total", "date", "items"]
