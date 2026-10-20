
from AdminSide.models import User, ApplicantProfile, EmployerProfile
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        error_messages = {
            'username': {
                'unique': "Invalid Username or Password.",
            },
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Invalid Username or Password.")

        return email

    def clean(self):
        return super().clean()


class BasicApplicantInformationForms(ModelForm):

    civil_status = forms.ChoiceField(
        choices=[
            ('', 'Select civil status')
        ] + list(ApplicantProfile.CIVIL_STATUS_CHOICES),
        required=False,
    )

    class Meta:
        model = ApplicantProfile
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'sex',
            'date_of_birth',
            'phone_number',
            'civil_status',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')

        if dob:
            today = timezone.localdate()

            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )

            if dob > today:
                raise ValidationError(
                    'Date of birth cannot be in the future.'
                )

            if age < 18:
                raise ValidationError(
                    'Applicant must be at least 18 years old.'
                )

        return dob

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')

        if phone and not phone.isdigit():
            raise ValidationError(
                'Phone number must contain numbers only.'
            )

        return phone


class BasicEmployerInformationForms(ModelForm):

    class Meta:
        model = EmployerProfile
        fields = [
            'business_name',
            'trade_name',
            'mobile_number',
            'owner_name',
            'email',
        ]

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')

        if mobile and not mobile.isdigit():
            raise ValidationError(
                'Mobile number must contain numbers only.'
            )

        return mobile

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email:
            return email.strip()

        return email


class SignInForm(forms.Form):

    email = forms.EmailField()

    password = forms.CharField(
        widget=forms.PasswordInput()
    )


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
