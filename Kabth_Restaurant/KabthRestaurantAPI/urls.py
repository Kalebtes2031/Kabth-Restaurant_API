from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/',views.menuitems.as_view(),name='menu_items'),
    path('menu-items/<int:pk>',views.SingleMenuItem.as_view()),
    path('category/',views.categories.as_view()),
    path('category/<int:pK>',views.SingleCategory.as_view()),
    path('cart/',views.Carts.as_view()),
    path('order/',views.Orders.as_view()), 
    path('orderitems/',views.OrderItems.as_view()), 
    path('groups/manager/assign/',views.assignusertomanager),
    path('groups/manager/users/',views.accessingmangergroup),
    path('token/login/',views.loginview),
    path('groups/delivery_crew/assign/',views.assignusertodeliverycrew),

]
