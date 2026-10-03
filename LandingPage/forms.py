from AdminSide.models import User,ApplicantProfile,EmployerProfile
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm,PasswordResetForm, SetPasswordForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class BasicApplicantInformationForms(ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = ['first_name','middle_name','last_name','sex','date_of_birth','phone_number']

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

class ForgotPasswordForm(PasswordResetForm):

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(
            subject_template_name,
            context
        ).strip()

        text_message = render_to_string(
            'LandingPage/ForgotPassword/password_reset_email.txt',
            context
        )

        html_message = render_to_string(
            'LandingPage/ForgotPassword/password_reset_email.html',
            context
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=[to_email],
        )

        email.attach_alternative(
            html_message,
            'text/html'
        )

        email.send()


class PasswordResetConfirmForm(SetPasswordForm):
    pass