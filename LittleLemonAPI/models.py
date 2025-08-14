from django.db import models
from django.contrib import admin

# Category
class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="items",on_delete=models.CASCADE)
    featured = models.BooleanField(default=False)

    
