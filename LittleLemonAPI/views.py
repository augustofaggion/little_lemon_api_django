from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, MenuItem, CartItem, Order, OrderItem
from .serializers import (
    UserSerializer, CategorySerializer, MenuItemSerializer,
    CartItemSerializer, OrderSerializer
)
from .permissions import IsAdmin, IsManager, IsDeliveryCrew, ReadOnly

# -------- Groups management --------

class ManagerUsersViewSet(viewsets.ViewSet):
    """
    Admin can assign/remove users to the Manager group.
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        grp = Group.objects.get(name="Manager")
        return Response(UserSerializer(grp.user_set.all(), many=True).data)

    def create(self, request):
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        grp = Group.objects.get(name="Manager")
        grp.user_set.add(user)
        return Response({"detail": f"{username} added to Manager"}, status=201)

    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        grp = Group.objects.get(name="Manager")
        grp.user_set.remove(user)
        return Response(status=204)

class DeliveryCrewUsersViewSet(viewsets.ViewSet):
    """
    Managers can assign/remove users to the Delivery crew.
    """
    permission_classes = [IsManager]

    def list(self, request):
        grp = Group.objects.get(name="Delivery crew")
        return Response(UserSerializer(grp.user_set.all(), many=True).data)

    def create(self, request):
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        grp = Group.objects.get(name="Delivery crew")
        grp.user_set.add(user)
        return Response({"detail": f"{username} added to Delivery crew"}, status=201)

    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        grp = Group.objects.get(name="Delivery crew")
        grp.user_set.remove(user)
        return Response(status=204)

# -------- Categories & Menu --------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer

    def get_permissions(self):
        # Admin can create/update/delete; everyone can read
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAdmin()]
        return [ReadOnly()]

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all().order_by("id")
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        # Admin can manage items; everyone can read; managers can set item-of-the-day via action below
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAdmin()]
        return [ReadOnly()]

    # filters: ?category=<id or slug>&ordering=price&search=<title>
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            # allow id or slug
            qs = qs.filter(category__id=category) | qs.filter(category__slug=category)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)
        ordering = self.request.query_params.get("ordering")
        if ordering in ["price", "-price"]:
            qs = qs.order_by(ordering)
        return qs

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsManager])
    def featured(self, request):
        """
        GET  /api/menu-items/featured/     -> current item of the day
        PATCH /api/menu-items/featured/ { "menuitem_id": <id> } -> set featured
        """
        if request.method.lower() == "get":
            item = MenuItem.objects.filter(featured=True).first()
            if not item:
                return Response({"detail": "No item set"}, status=204)
            return Response(MenuItemSerializer(item).data)
        # set: unset others, set this one
        mid = request.data.get("menuitem_id")
        item = get_object_or_404(MenuItem, pk=mid)
        MenuItem.objects.filter(featured=True).update(featured=False)
        item.featured = True
        item.save()
        return Response(MenuItemSerializer(item).data)

# -------- Cart --------

class CartViewSet(viewsets.ViewSet):
    """
    /api/cart/menu-items/  GET (list)
                           POST {menuitem_id, quantity}
                           DELETE (empty cart)
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        items = CartItem.objects.filter(user=request.user).select_related("menuitem")
        return Response(CartItemSerializer(items, many=True).data)

    def create(self, request):
        menuitem_id = request.data.get("menuitem_id")
        quantity = int(request.data.get("quantity", 1))
        menuitem = get_object_or_404(MenuItem, pk=menuitem_id)
        unit = menuitem.price
        price = Decimal(quantity) * unit
        item, created = CartItem.objects.get_or_create(
            user=request.user, menuitem=menuitem,
            defaults={"quantity": quantity, "unit_price": unit, "price": price}
        )
        if not created:
            item.quantity += quantity
            item.price = Decimal(item.quantity) * item.unit_price
            item.save()
        return Response(CartItemSerializer(item).data, status=201)

    def destroy(self, request, pk=None):
        # Empty entire cart (ignore pk)
        CartItem.objects.filter(user=request.user).delete()
        return Response(status=204)

# -------- Orders --------

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.select_related("user", "delivery_crew").prefetch_related("items__menuitem").order_by("-date")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_staff or user.groups.filter(name="Manager").exists():
            # managers/admins see all orders
            return qs
        if user.groups.filter(name="Delivery crew").exists():
            # delivery crew sees assigned orders
            return qs.filter(delivery_crew=user)
        # customers see their own orders
        return qs.filter(user=user)

    def create(self, request, *args, **kwargs):
        """
        Customers place an order from their cart.
        """
        user = request.user
        cart_items = CartItem.objects.filter(user=user).select_related("menuitem")
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=400)
        total = sum(i.price for i in cart_items)
        order = Order.objects.create(user=user, total=total)
        bulk = []
        for ci in cart_items:
            bulk.append(OrderItem(
                order=order,
                menuitem=ci.menuitem,
                quantity=ci.quantity,
                unit_price=ci.unit_price,
                price=ci.price
            ))
            # reduce inventory (basic)
            ci.menuitem.inventory = max(0, ci.menuitem.inventory - ci.quantity)
            ci.menuitem.save()
        OrderItem.objects.bulk_create(bulk)
        cart_items.delete()
        return Response(OrderSerializer(order).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        """
        Managers can assign delivery_crew OR update status.
        Delivery crew can update status to delivered for their orders.
        """
        order = self.get_object()
        user = request.user

        # manager/admin: can assign crew and set status
        if user.is_staff or user.groups.filter(name="Manager").exists():
            if "delivery_crew_id" in request.data:
                return super().partial_update(request, *args, **kwargs)
            if "status" in request.data:
                return super().partial_update(request, *args, **kwargs)

        # delivery crew: only for their orders, mark delivered
        if user.groups.filter(name="Delivery crew").exists():
            if order.delivery_crew_id != user.id:
                return Response({"detail": "Not your order."}, status=403)
            status_value = request.data.get("status")
            if str(status_value) == str(Order.STATUS_DELIVERED):
                order.status = Order.STATUS_DELIVERED
                order.save()
                return Response(OrderSerializer(order).data)
            return Response({"detail": "Delivery crew can only mark delivered."}, status=403)

        return Response({"detail": "Not allowed."}, status=403)
