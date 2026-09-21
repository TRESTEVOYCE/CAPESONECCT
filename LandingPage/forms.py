from AdminSide.models import User,ApplicantProfile,EmployerProfile
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class BasicApplicantInformationForms(ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = ['first_name','middle_name','last_name','sex','phone_number']

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class BasicEmployerInformationForms(ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['business_name','trade_name','mobile_number','owner_name','email']

class SignInForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField()