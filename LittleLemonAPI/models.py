# LittleLemonAPI/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    def __str__(self):
        return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="items", on_delete=models.CASCADE)
    featured = models.BooleanField(default=False)  # “item of the day”

    class Meta:
        unique_together = ("title", "category")

    def __str__(self):
        return f"{self.title} ({self.category})"

class CartItem(models.Model):
    user = models.ForeignKey(User, related_name="cart_items", on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("user", "menuitem")

    def __str__(self):
        return f"{self.user} – {self.menuitem} x{self.quantity}"

class Order(models.Model):
    STATUS_PENDING = 0
    STATUS_OUT_FOR_DELIVERY = 1
    STATUS_DELIVERED = 2
    STATUS_CHOICES = (
        (STATUS_PENDING, "pending"),
        (STATUS_OUT_FOR_DELIVERY, "out for delivery"),
        (STATUS_DELIVERED, "delivered"),
    )

    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(
        User, related_name="deliveries", on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Order #{self.order_id} – {self.menuitem} x{self.quantity}"
