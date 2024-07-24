# middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get URLs
        login_url = reverse('login')
        logout_url = reverse('logout')

        # Handle unauthenticated users
        if not request.user.is_authenticated:
            if request.path not in [login_url, logout_url]:
                return redirect(login_url)
        # Handle authenticated users
        elif request.path == login_url:
            return redirect(reverse('home'))

        response = self.get_response(request)
        return response
