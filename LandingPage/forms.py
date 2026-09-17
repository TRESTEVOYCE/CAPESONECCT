from AdminSide.models import User
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class SignInForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField()