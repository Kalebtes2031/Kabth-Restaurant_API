from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=63)
    password = forms.CharField(widget=forms.PasswordInput)
