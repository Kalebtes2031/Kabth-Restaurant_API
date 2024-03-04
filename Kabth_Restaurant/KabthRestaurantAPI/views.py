from rest_framework import generics
from .serializers import MenuItemSerializer, UserSerializer, UserCartSerializer, UserOrdersSerializer
from .models import MenuItem, OrderItem, Cart, Order
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User, Group
from rest_framework.response import Response
from decimal import Decimal
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle



class MenuItemView(generics.ListAPIView, generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    search_fields = ['title']
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView, generics.RetrieveAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        if self.request.method == 'POST' or self.request.method == 'PUT' \
                or self.request.method == 'DELETE' or self.request.method == 'PATCH':
            return [IsAdminUser()]
        return [AllowAny()]

class Carts(generics.ListCreateAPIView):
    serializer_class = UserCartSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user=user)

    def perform_create(self, serializer):
        menuitem = self.request.data.get('menuitem')
        quantity = self.request.data.get('quantity')
        unit_price = MenuItem.objects.get(pk=menuitem).price
        quantity = int(quantity)
        price = quantity * unit_price
        serializer.save(user=self.request.user, price=price)

    def delete(self, request):
        user = self.request.user
        Cart.objects.filter(user=user).delete()
        return Response(status=204)

class OrdersView(generics.ListCreateAPIView):
    serializer_class = UserOrdersSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        total = self.calculate_total(cart_items)
        order = serializer.save(user=self.request.user, total=total)

        for cart_item in cart_items:
            OrderItem.objects.create(
                menuitem=cart_item.menuitem, 
                quantity=cart_item.quantity,
                unit_price=cart_item.menuitem.price,
                price=cart_item.price, order=order
                )
            cart_item.delete()

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def calculate_total(self, cart_items):
        total = Decimal(0)
        for item in cart_items:
            total += item.price
        return total

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserOrdersSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

class ManagerUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name='manager')
        queryset = User.objects.filter(groups=manager_group)
        return queryset

    def perform_create(self, serializer):
        manager_group = Group.objects.get(name='manager')
        user = serializer.save()
        user.groups.add(manager_group)

class SingleManagerUserView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # Get the 'manager' group
        manager_group = Group.objects.get(name='manager')
        # Get the users in the 'manager' group
        queryset = User.objects.filter(groups=manager_group)
        return queryset

class DeliveryCrewView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery Crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset

    def perform_create(self, serializer):
        delivery_group = Group.objects.get(name='Delivery Crew')
        user = serializer.save()
        user.groups.add(delivery_group)

class SingleDeliveryCrewView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery Crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset
