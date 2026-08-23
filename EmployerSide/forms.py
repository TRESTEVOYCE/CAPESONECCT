from django import forms 
from AdminSide.models import EmployerProfile,Jobs


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = '__all__'

class JobsForm(forms.ModelForm):
    class Meta:
        model = Jobs
        fields = '__all__'