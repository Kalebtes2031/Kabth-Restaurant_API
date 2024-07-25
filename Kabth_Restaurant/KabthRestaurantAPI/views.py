from rest_framework import generics
from .serializers import MenuItemSerializer, UserSerializer, UserCartSerializer, UserOrdersSerializer
from .models import MenuItem, OrderItem, Cart, Order
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User, Group
from rest_framework.response import Response
from rest_framework.decorators import api_view
from decimal import Decimal
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal
from .forms import LoginForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
import requests, logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST



logger = logging.getLogger(__name__)


@api_view(['POST'])
def custom_logout(request):
    logger.info("Logout request received")
    auth_logout(request)
    request.session.flush()
    logger.info("User logged out")
    return JsonResponse({'message': 'Logged out successfully'}, status=204)


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Incorrect username or password')
        return render(request, 'login.html', {'form': form})
    

class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'home.html')

@login_required
def about(request):
    return render(request, 'about.html')


@method_decorator(login_required, name='dispatch')
class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    search_fields = ['title']
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        menu_contents = MenuItem.objects.all()
        return render(request, 'menu.html', {"menu": menu_contents})

@method_decorator(login_required, name='dispatch')
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'POST' or self.request.method == 'PUT' \
                or self.request.method == 'DELETE' or self.request.method == 'PATCH':
            return [IsAdminUser()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        menu_item = get_object_or_404(MenuItem, pk=pk)
        return render(request, "menu_item.html", {"menu_item": menu_item})


@method_decorator(login_required, name='dispatch')   
class Carts(generics.ListCreateAPIView):
    serializer_class = UserCartSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user=user)

    # def perform_create(self, serializer):
    #     menuitem = self.request.data.get('menuitem')
    #     quantity = self.request.data.get('quantity')
    #     unit_price = MenuItem.objects.get(pk=menuitem).price
    #     quantity = int(quantity)
    #     price = quantity * unit_price
    #     serializer.save(user=self.request.user, price=price)

    def post(self, request, *args, **kwargs):
        menuitem_id = request.POST.get('menuitem')
        quantity = request.POST.get('quantity')

        if not menuitem_id or not quantity:
            return Response({"error": "Menu item and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menuitem = MenuItem.objects.get(pk=menuitem_id)
            quantity = int(quantity)
        except (MenuItem.DoesNotExist, ValueError):
            return Response({"error": "Invalid menu item or quantity."}, status=status.HTTP_400_BAD_REQUEST)

        unit_price = menuitem.price
        price = quantity * unit_price

        # Check if the item already exists in the cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            menuitem_id=menuitem_id,
            defaults={'quantity': quantity, 'price': price}
        )

        if not created:
            # If the cart item already exists, update the quantity and price
            cart_item.quantity += quantity
            cart_item.price += price
            cart_item.save()

        return redirect('cart')


    def delete(self, request):
        user = self.request.user
        Cart.objects.filter(user=user).delete()
        return Response(status=204)
    def list(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=self.request.user).select_related('menuitem')
        return render(request, 'cart.html', {"cart_items": cart_items})
    

@login_required
def delete_cart_item(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')

@method_decorator(login_required, name='dispatch')
class OrdersView(generics.ListCreateAPIView):
    serializer_class = UserOrdersSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def create(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=self.request.user)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        total = self.calculate_total(cart_items)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user=self.request.user, total=total)
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                menuitem=cart_item.menuitem, 
                quantity=cart_item.quantity,
                unit_price=cart_item.menuitem.price,
                price=cart_item.price, order=order
                )
            cart_item.delete()
        return redirect('orders')
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def calculate_total(self, cart_items):
        total = Decimal(0)
        for item in cart_items:
            total += item.price
        return total

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = {
            'orders': queryset
        }
        return render(request, 'orders.html', context)
    
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user == request.user or request.user.groups.filter(name='Manager').exists():
        order.delete()
    return redirect('orders')


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserOrdersSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get(self, request, *args, **kwargs):
        # Retrieve the order object
        order = self.get_object()
        order_items = OrderItem.objects.filter(order=order)
        
        # Render the template for a regular HTTP request
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'order_item.html', context)

class ManagerUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name='Manager')
        queryset = User.objects.filter(groups=manager_group)
        return queryset

    def perform_create(self, serializer):
        manager_group = Group.objects.get(name='Manager')
        user = serializer.save()
        user.groups.add(manager_group)

class SingleManagerUserView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # Get the 'manager' group
        manager_group = Group.objects.get(name='Manager')
        # Get the users in the 'manager' group
        queryset = User.objects.filter(groups=manager_group)
        return queryset

class DeliveryCrewView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset

    def perform_create(self, serializer):
        delivery_group = Group.objects.get(name='Delivery crew')
        user = serializer.save()
        user.groups.add(delivery_group)

class SingleDeliveryCrewView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        delivery_group = Group.objects.get(name='Delivery crew')
        queryset = User.objects.filter(groups=delivery_group)
        return queryset

# class MenuItemView(generics.ListAPIView, generics.ListCreateAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer
#     ordering_fields = ['price']
#     search_fields = ['title']
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]
#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return [IsAdminUser()]
#         return [AllowAny()]
    
# class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView, generics.RetrieveAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]
#     def get_permissions(self):
#         if self.request.method == 'POST' or self.request.method == 'PUT' \
#                 or self.request.method == 'DELETE' or self.request.method == 'PATCH':
#             return [IsAdminUser()]
#         return [AllowAny()]