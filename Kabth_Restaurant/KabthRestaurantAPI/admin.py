from django.contrib import admin
from .models import Category, MenuItem,Order,OrderItem,Cart

admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)