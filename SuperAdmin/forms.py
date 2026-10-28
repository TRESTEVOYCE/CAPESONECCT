from AdminSide.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class LoginForm(forms.Form):

    email = forms.EmailField()
    password = forms.CharField()


class MSWDOAccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].required = True
        self.fields['email'].required = True

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username',
        })

        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter email address',
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password',
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'mswdo'

        if commit:
            user.save()
            self.save_m2m()

        return user

class PESOAccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].required = True
        self.fields['email'].required = True

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter email address',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'peso'

        if commit:
            user.save()
            self.save_m2m()

        return user
