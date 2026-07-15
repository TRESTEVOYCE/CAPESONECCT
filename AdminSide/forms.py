from .models import User,SpecialProgramBeneficiaries
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email','password1', 'password2') 

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('email', 'password')

class SpecialProgramBeneferiariesForm(forms.ModelForm):
    class Meta:
        model = SpecialProgramBeneficiaries
        fields = ('first_name','middle_name','last_name','email','phone_number','address','city','state','zip_code','daily_salary','start_date','end_date')

