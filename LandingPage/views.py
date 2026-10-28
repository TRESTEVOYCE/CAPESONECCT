from django.views.generic import FormView, TemplateView, RedirectView, UpdateView
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.decorators import method_decorator
from honeypot.decorators import check_honeypot
from AdminSide.models import ApplicantProfile, EmployerProfile, User
from AdminSide.utils import notify_admins
from AdminSide.tokens import account_activation_token
from .forms import UserRegisterForm,SignInForm,BasicApplicantInformationForms,BasicEmployerInformationForms,ForgotPasswordForm,PasswordResetConfirmForm
from django.contrib.auth.views import PasswordResetView,PasswordResetDoneView,PasswordResetConfirmView,PasswordResetCompleteView
from django.views import View
from datetime import timedelta


class Register_SelectionView(TemplateView):
    template_name = 'LandingPage/register_selection.html'


@method_decorator(check_honeypot, name='dispatch')
class UserApplicantRegisterView(FormView):
    template_name = 'LandingPage/register_jobseeker.html'
    form_class = BasicApplicantInformationForms

    def form_valid(self, form):
        self.request.session['applicant_info'] = {
            **form.cleaned_data,
            'date_of_birth': form.cleaned_data['date_of_birth'].isoformat(),
        }
        return redirect('applicant-account-register')


@method_decorator(check_honeypot, name='dispatch')
class UserApplicantAccountRegisterView(FormView):
    template_name = 'LandingPage/register_jobseeker_account.html'
    form_class = UserRegisterForm

    def form_valid(self, form):
        info = self.request.session.get('applicant_info')

        if not info:
            return redirect('register_jobseeker')

        email = form.cleaned_data.get('email')

        # Avoid revealing whether an email already has an account.
        if User.objects.filter(email=email).exists():
            self.request.session.pop('applicant_info', None)
            messages.info(
                self.request,
                'If you already registered, please sign in or use the appropriate account recovery option.'
            )
            return redirect('signin')

        user = form.save(commit=False)
        user.role = 'applicant'
        user.email_verified = False
        user.email_verification_sent_at = None
        user.save()

        # Remember which account needs email verification.
        self.request.session['pending_verification_user_id'] = user.pk

        info['civil_status'] = (
            (info.get('civil_status') or '').strip() or 'single'
        )

        applicant = ApplicantProfile.objects.create(
            user=user,
            **info
        )

        notify_admins(
            title='New Applicant',
            message=(
                f'{applicant.first_name} {applicant.last_name} '
                'completed applicant registration.'
            ),
            notification_type='NEW_APPLICANT',
            sender=user,
            target_url=reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': applicant.uuid}
            ),
        )

        self.request.session.pop('applicant_info', None)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_url = self.request.build_absolute_uri(
            reverse(
                'activate',
                kwargs={
                    'uidb64': uid,
                    'token': token,
                }
            )
        )

        try:
            sent = send_mail(
                subject='Verify Your CAPESCONNECT Account',
                message=f"""
                    Hello {user.username},

                    Thank you for registering with CAPESCONNECT.

                    Please verify your email address by clicking the link below:

                    {activation_url}

                    This verification link will expire after 24 hours.

                    After verifying your email, you will automatically be logged in and redirected to your applicant dashboard.

                    If you did not create this account, please ignore this email.

                    Regards,
                    CAPESCONNECT
                    """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            if sent:
                user.email_verification_sent_at = timezone.now()
                user.save(update_fields=['email_verification_sent_at'])

        except Exception:
            # Log the exception in production.
            messages.warning(
                self.request,
                'Your account was created, but the verification email '
                'could not be sent. Please use the resend option below.'
            )

        return redirect('verify-email')


@method_decorator(check_honeypot, name='dispatch')
class UserEmployerRegisterView(FormView):
    template_name = 'LandingPage/register_employer.html'
    form_class = BasicEmployerInformationForms

    def form_valid(self, form):
        self.request.session['employer_info'] = form.cleaned_data
        return redirect('employer-account-register')


@method_decorator(check_honeypot, name='dispatch')
class UserEmployerAccountRegisterView(FormView):
    template_name = 'LandingPage/register_employer_account.html'
    form_class = UserRegisterForm

    def form_valid(self, form):
        info = self.request.session.get('employer_info')

        if not info:
            return redirect('register_employer')

        email = form.cleaned_data.get('email')

        # Avoid revealing whether an email already has an account.
        if User.objects.filter(email=email).exists():
            self.request.session.pop('employer_info', None)
            messages.info(
                self.request,
                'If you already registered, please sign in or use the appropriate account recovery option.'
            )
            return redirect('signin')

        user = form.save(commit=False)
        user.role = 'employer'
        user.email_verified = False
        user.email_verification_sent_at = None
        user.save()

        # Remember which account needs email verification.
        self.request.session['pending_verification_user_id'] = user.pk

        employer, _ = EmployerProfile.objects.update_or_create(
            user=user,
            defaults=info
        )

        notify_admins(
            title='New Employer',
            message=(
                f'{employer.business_name or user.username} '
                'submitted an employer profile for verification.'
            ),
            notification_type='NEW_EMPLOYER',
            sender=user,
            target_url=reverse(
                'AdminSide:employer_verification',
                kwargs={'uuid': employer.uuid}
            ),
        )

        self.request.session.pop('employer_info', None)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_url = self.request.build_absolute_uri(
            reverse(
                'activate',
                kwargs={
                    'uidb64': uid,
                    'token': token,
                }
            )
        )

        try:
            sent = send_mail(
                subject='Verify Your CAPESCONNECT Account',
                message=f"""
                    Hello {user.username},

                    Thank you for registering with CAPESCONNECT.

                    Please verify your email address by clicking the link below:

                    {activation_url}

                    This verification link will expire after 24 hours.

                    After verifying your email, you will automatically be logged in and redirected to your applicant dashboard.

                    If you did not create this account, please ignore this email.

                    Regards,
                    CAPESCONNECT
                    """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            if sent:
                user.email_verification_sent_at = timezone.now()
                user.save(update_fields=['email_verification_sent_at'])

        except Exception:
            # Log the exception in production.
            messages.warning(
                self.request,
                'Your account was created, but the verification email '
                'could not be sent. Please use the resend option below.'
            )

        return redirect('verify-email')

class VerifyEmailView(TemplateView):
    template_name = 'LandingPage/verify_email.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.email_verified:
            if request.user.role == 'applicant':
                return redirect('applicant-dashboard')
            if request.user.role == 'employer':
                return redirect('employer-home')

        return super().dispatch(request, *args, **kwargs)


@method_decorator(check_honeypot, name='dispatch')
class SignInView(FormView):
    form_class = SignInForm
    template_name = 'LandingPage/signin.html'

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(
            self.request,
            email=email,
            password=password
        )

        if not user:
            form.add_error(None, 'Invalid email or password.')
            return self.form_invalid(form)

        # Redirect unverified users to the verification page.
        if not user.email_verified:
            self.request.session['pending_verification_user_id'] = user.pk

            messages.info(
                self.request,
                'Your email has not been verified yet. '
                'Please verify your email or request a new verification email.'
            )

            return redirect('verify-email')

        # Log in verified users.
        login(self.request, user)

        if user.role == 'applicant':
            return redirect('applicant-dashboard')

        if user.role == 'employer':
            return redirect('employer-home')

        return redirect('landing_page')



class LandingPageView(TemplateView):
    template_name = 'LandingPage/index.html'


class ActivateAccountView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and account_activation_token.check_token(user, token):
            if not user.email_verified:
                user.email_verified = True
                user.email_verification_sent_at = None
                user.save(update_fields=[
                    'email_verified',
                    'email_verification_sent_at',
                ])

            login(
                self.request,
                user,
                backend='django.contrib.auth.backends.ModelBackend'
            )

            messages.success(
                self.request,
                'Your email has been verified successfully.'
            )

            if user.role == 'applicant':
                return reverse_lazy('applicant-dashboard')

            if user.role == 'employer':
                return reverse_lazy('employer-home')

            return reverse_lazy('landing_page')

        messages.error(
            self.request,
            'Invalid or expired verification link.'
        )
        return reverse_lazy('signin')
    
class ForgotPasswordView(PasswordResetView):
    template_name = 'LandingPage/ForgotPassword/forgot_password.html'
    form_class = ForgotPasswordForm
    subject_template_name = 'LandingPage/ForgotPassword/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_sent')


class PasswordResetSentView(PasswordResetDoneView):
    template_name = 'LandingPage/ForgotPassword/password_reset_sent.html'


class PasswordResetChangeView(PasswordResetConfirmView):
    template_name = 'LandingPage/ForgotPassword/password_reset_confirm.html'
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy('password_reset_complete')


class PasswordResetSuccessView(PasswordResetCompleteView):
    template_name = 'LandingPage/ForgotPassword/password_reset_complete.html'
    
class TermsAndConditionsView(TemplateView):
    template_name = 'LandingPage/terms_and_conditions.html'
    
class PrivacyPolicyView(TemplateView):
    template_name = 'LandingPage/privacy_policy.html'


class EmployerTermsAndConditionsView(TemplateView):
    template_name = 'LandingPage/terms_and_conditions_employer.html'
    
class EmployerPrivacyPolicyView(TemplateView):
    template_name = 'LandingPage/privacy_policy_employer.html'


class ResendVerificationEmailView(View):

    def post(self, request, *args, **kwargs):
        user_id = request.session.get(
            'pending_verification_user_id'
        )

        if not user_id:
            messages.error(
                request,
                'Your verification session has expired. '
                'Please register or sign in again.'
            )
            return redirect('signin')

        user = User.objects.filter(
            pk=user_id,
            email_verified=False
        ).first()

        if not user:
            request.session.pop(
                'pending_verification_user_id',
                None
            )
            messages.error(
                request,
                'No pending email verification was found.'
            )
            return redirect('signin')

        # Prevent repeated requests within two minutes.
        now = timezone.now()
        last_sent = user.email_verification_sent_at

        if last_sent and now - last_sent < timedelta(minutes=2):
            messages.info(
                request,
                'Please wait two minutes between verification '
                'email requests.'
            )
            return redirect('verify-email')

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_url = request.build_absolute_uri(
            reverse(
                'activate',
                kwargs={
                    'uidb64': uid,
                    'token': token,
                }
            )
        )

        try:
            sent = send_mail(
                subject='Verify Your CAPESCONNECT Account',
                message=(
                    f'Hello {user.username},\n\n'
                    'Please verify your CAPESCONNECT account '
                    'using the link below:\n\n'
                    f'{activation_url}\n\n'
                    'This verification link will expire after '
                    '24 hours.\n\n'
                    'If you did not create this account, '
                    'please ignore this email.\n\n'
                    'Regards,\nCAPESCONNECT'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            if sent:
                user.email_verification_sent_at = now
                user.save(
                    update_fields=['email_verification_sent_at']
                )

                messages.success(
                    request,
                    'A new verification email has been sent. '
                    'Please check your inbox and spam folder.'
                )
            else:
                messages.error(
                    request,
                    'We could not send the verification email. '
                    'Please try again later.'
                )

        except Exception:
            # Log the exception in production.
            messages.error(
                request,
                'Unable to send the verification email right now. '
                'Please try again later.'
            )

        return redirect('verify-email')