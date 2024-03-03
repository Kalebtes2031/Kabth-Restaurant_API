from django.shortcuts import render
from rest_framework import generics,status
from .models import Order,MenuItem,Category,Cart,OrderItem
from .serializers import MenuItemSerializer,CategorySerializer,CartSerializer,OrderSerializer,OrderItemSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from django.contrib.auth.models import User,Group
from rest_framework.decorators import api_view, permission_classes
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

class menuitems(generics.ListCreateAPIView):
    permission_classes=[IsAuthenticated]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    ordering_fields = ['price','title']
    search_fields = ['title','price','category__title']



class SingleMenuItem(generics.RetrieveUpdateAPIView,generics.DestroyAPIView):
    permission_classes=[IsAuthenticated]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    def has_permission(self):
        user = self.request.user
        manager = Group.objects.get(name='Manager')
        if user.is_superuser or manager in user.groups.all():
            return True
        else:
            return False
    def get(self, request, *args, **kwargs):
        if not self.has_permission():
            raise PermissionDenied("You do not have permission to perform this action.")
        return super().get(request, *args, **kwargs)
    def put(self,request, *args, **kwargs):
        if not self.has_permission():
            raise PermissionDenied("You don't have permission to perform this action")
        return super().put(request,*args,**kwargs)
    def delete(self,request, *args, **kwargs):
        if not self.has_permission():
            raise PermissionDenied("You don't have permission to perform this action")
        return super().delete(request,*args,**kwargs)
    
        

class categories(generics.ListAPIView):
    permission_classes=[IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SingleCategory(generics.RetrieveUpdateAPIView,generics.DestroyAPIView):
    permission_classes=[IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class Carts(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
        
class Orders(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    def create(self, request, *args, **kwargs):
        # Retrieve the current user's cart items
        user_cart_items = Cart.objects.filter(user=request.user)

        # Create an order with the provided data
        order_serializer = self.get_serializer(data=request.data)
        if order_serializer.is_valid():
            order = order_serializer.save()

            # Create order items from the user's cart items using OrderItem serializer
            order_items_serializer = OrderItemSerializer(data=[
                {
                    'order': order.id,
                    'menuitem': cart_item.menuitem_id,
                    'quantity': cart_item.quantity,
                }
                for cart_item in user_cart_items
            ], many=True)

            if order_items_serializer.is_valid():
                order_items_serializer.save()
                # Clear the user's cart after creating the order
                user_cart_items.delete()
                return Response(order_serializer.data, status=status.HTTP_201_CREATED)
            else:
                order.delete()  # Delete the order if order items creation fails
                return Response(order_items_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #def create(self, request, *args, **kwargs):
     #   order_serializer = self.get_serializer(data=request.data.get('order'))
      #  if order_serializer.is_valid():
       #     order = order_serializer.save()
#
 #           order_items_data = request.data.get('order_items')
  #          order_items_serializer = OrderItemSerializer(data=order_items_data, many=True)
   #         if order_items_serializer.is_valid():
    #            order_items_serializer.save(order=order)
     #           order.update_total_price()  # Update total price after saving items
      #          headers = self.get_success_headers(order_items_serializer.data)
       #         return Response(order_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        #    else:
         #       return Response(order_items_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #else:
         #   return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderItems(generics.ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def create(self, request, *args, **kwargs):
        print("Request Data:", request.data)
        order_id = request.data.get('order')  # Assuming the order ID is provided in the request
        order = get_object_or_404(Order, pk=order_id)

        user_cart_items = Cart.objects.filter(user=request.user)

        order_items_data = [
            {
                'order': order_id,
                'menuitem': cart_item.menuitem_id,
                'quantity': cart_item.quantity,
            }
            for cart_item in user_cart_items
        ]

        order_item_serializer = self.get_serializer(data=order_items_data, many=True)
        if order_item_serializer.is_valid():
            order_items = order_item_serializer.save()

            # Clear the user's cart after creating the order items
            user_cart_items.delete()

            return Response(order_item_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
@permission_classes([IsAdminUser])
def assignusertomanager(request):
    try:
        username = request.data.get('username')
        user = User.objects.get(username=username)
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response({"message": f"{username} has been assigned to the manager group."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
    except Group.DoesNotExist:
        return Response({"message": "Manager group does not exist."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST','GET'])
@permission_classes([IsAdminUser])
def accessingmangergroup(request):
    try:
        managers=Group.objects.get(name='Manager')
        managers_user = managers.user_set.all()

        for user in managers_user:
            print(user.username)
        
        return Response({'message':f"you accessed {user.username} the manager group successfully"},status.HTTP_201_CREATED)
    except Group.DoesNotExist:
        return Response({"message": "Manager group does not exist."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view()
@permission_classes([IsAuthenticated])
def loginview(request):
    try:
        user = request.user
        manager_group = Group.objects.get(name='Manager')
        
        if user.is_superuser or manager_group in user.groups.all():
            return HttpResponseRedirect(reverse('menu_items'))
        else:
            return Response({"message": "You are not authorized to access this resource"}, status=status.HTTP_403_FORBIDDEN)
    except Group.DoesNotExist:
        return Response({"message": "Manager group does not exist"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def assignusertodeliverycrew(request):
    try:
        user = request.user
        manager_group = Group.objects.get(name='Manager')       
        if manager_group in user.groups.all():
            username= request.data.get('username')
            user = User.objects.get(username=username)
            delivery_crew =Group.objects.get(name='Delivery crew')
            delivery_crew.user_set.add(user)
            return Response({"message": f"{username} has been assigned to the delivery group."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
    except Group.DoesNotExist:
        return Response({"message": "Manager group does not exist."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
