# LittleLemonAPI/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, MenuItemViewSet, CartViewSet, OrderViewSet,
    ManagerUsersViewSet, DeliveryCrewUsersViewSet
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"menu-items", MenuItemViewSet, basename="menuitem")
router.register(r"cart/menu-items", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"groups/manager/users", ManagerUsersViewSet, basename="manager-users")
router.register(r"groups/delivery-crew/users", DeliveryCrewUsersViewSet, basename="delivery-users")

urlpatterns = [
    path("", include(router.urls)),
]
