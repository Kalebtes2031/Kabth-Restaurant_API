from django.contrib import admin
from django.urls import path, include
from KabthRestaurantAPI import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('KabthRestaurantAPI.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
