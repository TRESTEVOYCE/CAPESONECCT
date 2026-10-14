from AdminSide.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password


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
        user.role = 'peso'

        if commit:
            user.save()
            self.save_m2m()

        return user
    
class StaffAccountUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10',
            'placeholder': 'Leave blank to keep current password',
            'autocomplete': 'new-password',
        }),
        validators=[validate_password],
    )

    confirm_password = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10',
            'placeholder': 'Re-enter new password',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in ['username', 'email']:
            self.fields[field].required = True
            self.fields[field].widget.attrs.update({
                'class': 'w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10',
            })

        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if not password:
                self.add_error('password', 'Please enter a new password.')

            if not confirm_password:
                self.add_error('confirm_password', 'Please confirm the new password.')

            if password and confirm_password and password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user


class SuperAdminPasswordConfirmForm(forms.Form):
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3 text-sm",
            "placeholder": "Enter your current password",
            "autocomplete": "current-password",
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user or not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password
