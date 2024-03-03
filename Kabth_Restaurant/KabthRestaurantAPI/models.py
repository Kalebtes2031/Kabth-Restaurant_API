from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)
    def __str__(self) -> str:
        return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index = True)
    price = models.DecimalField(max_digits=6,decimal_places=2,db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    def __str__(self) -> str:
        return self.title

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    @property
    def unit_price(self):
        return self.menuitem.price
    
    @property
    def price(self):
        return self.quantity * self.unit_price
    @property
    def total_price(self):
        total = Decimal(0)
        # Iterate over all Cart objects associated with the same user
        for cart in Cart.objects.filter(user=self.user):
            total += cart.price  # Add the price of each item to the total
        return total

    class Meta:
        unique_together = ('menuitem','user')

class Order(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    status = models.BooleanField(db_index=True,default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    date = models.DateField(db_index=True)

   # def save(self, *args, **kwargs):
    #    self.total = sum(item.price for item in self.order_items.all())
     #   super().save(*args, **kwargs)

    def calculate_total_price(self):
        carts = Cart.objects.filter(user=self.user)
        total_price = sum(cart.price for cart in carts)
        return total_price

class OrderItem(models.Model):
    order = models.ForeignKey(Order,related_name='order_items', on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def save(self, *args, **kwargs):
        self.unit_price = self.menuitem.price
        self.price = self.unit_price * self.quantity  # Corrected calculation
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('order', 'menuitem')