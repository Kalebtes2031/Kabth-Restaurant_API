from rest_framework import serializers
from .models import MenuItem, Category,Cart,Order,OrderItem
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User,Group

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id','title','price','category','featured']
        extra_kwargs = {
            'price' : {'min_value':2}
        }

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title']


class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default = serializers.CurrentUserDefault()
    )
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    class Meta:
        model = Cart
        fields = ['id','user','menuitem','quantity','unit_price','price','total_price']
        validators = [UniqueTogetherValidator(
            queryset=Cart.objects.all(),
            fields=['menuitem','user']
        )]
        extra_kwargs = {
            'quantity ' : {'min_value': 1}
        }
    
class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    # Define the serializer field for the delivery_crew attribute
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        required=False
    )
    total = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']

    def create(self, validated_data):
        order = super().create(validated_data)
        total_price = order.calculate_total_price()
        order.total = total_price
        order.save()
        return order

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        total_price = instance.calculate_total_price()
        instance.total = total_price
        instance.save()
        return instance
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price','price']