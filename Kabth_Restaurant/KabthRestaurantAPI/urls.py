from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('login/', views.LoginView.as_view(), name='login'),
    # path('logout/', views.CustomLogoutView.as_view(), name='logout'),   
    path('home/', views.HomeView.as_view(), name='home'),
    # path('', views.custom_login, name='login'),
    # path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    # path('home/', views.home, name='home'),
    path('menu/', views.MenuItemView.as_view(), name='menu'),
    path('menu/<int:pk>/', views.SingleMenuItemView.as_view(), name ='menu_item'),
    path('cart/', views.Carts.as_view(),name='cart'),
    path('orders/', views.OrdersView.as_view(),name='orders'),
    path('orders/<int:pk>/', views.SingleOrderView.as_view(),name='order_item'),
    path('groups/manager/users/', views.ManagerUsersView.as_view()),
    path('groups/manager/users/<int:pk>/', views.SingleManagerUserView.as_view()),
    path('groups/delivery-crew/users/', views.DeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>/', views.SingleDeliveryCrewView.as_view()),
    path('about/',views.about, name='about'),
]
