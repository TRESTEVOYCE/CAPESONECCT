from .models import User,GovernmentInternshipProgram,TupadBeneficiary,DisplacedInformalLaborProgram,SpecialProgramForEmploymentOfStudents
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

class GovernmentInternshipProgramForm(forms.ModelForm):
    class Meta:
        model = GovernmentInternshipProgram
        fields = ('first_name','middle_name','last_name','email','phone_number','address','city','state','zip_code','daily_salary','start_date','end_date')

class TupadBeneficiaryForm(forms.ModelForm):
    class Meta:
        model = TupadBeneficiary
        fields = ('first_name','middle_name','last_name','email','phone_number','address','city','state','zip_code','daily_salary','start_date','end_date')

class DisplacedInformalLaborProgramForm(forms.ModelForm):
    class Meta:
        model = DisplacedInformalLaborProgram
        fields = ('first_name','middle_name','last_name','email','phone_number','address','city','state','zip_code','daily_salary','start_date','end_date')

class SpecialProgramForEmploymentOfStudentsForm(forms.ModelForm):
    class Meta:
        model = SpecialProgramForEmploymentOfStudents
        fields = ('first_name','middle_name','last_name','email','phone_number','address','city','state','zip_code','daily_salary','start_date','end_date')
