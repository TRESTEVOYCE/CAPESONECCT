from django.views.generic import FormView, TemplateView
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from honeypot.decorators import check_honeypot
from django.utils.decorators import method_decorator
from AdminSide.models import ApplicantProfile,EmployerProfile
from .forms import UserRegisterForm,SignInForm,BasicApplicantInformationForms,BasicEmployerInformationForms


class Register_SelectionView(TemplateView):
    template_name = 'LandingPage/register_selection.html'

# APPLICANT REGISTRATION
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
    success_url = reverse_lazy('applicant-dashboard')

    def form_valid(self, form):
        info = self.request.session.get('applicant_info')

        if not info:
            return redirect('register_jobseeker')

        user = form.save(commit=False)
        user.role = 'applicant'
        user.save()

        ApplicantProfile.objects.create(
            user=user,
            **info
        )

        del self.request.session['applicant_info']

        login(self.request, user)

        return redirect(self.success_url)


# EMPLOYER REGISTRATION
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
    success_url = reverse_lazy('employer-home')

    def form_valid(self, form):
        info = self.request.session.get('employer_info')

        if not info:
            return redirect('register_employer')

        user = form.save(commit=False)
        user.role = 'employer'
        user.save()

        EmployerProfile.objects.update_or_create(
            user=user,
            defaults=info
        )

        del self.request.session['employer_info']

        login(self.request, user)

        return redirect(self.success_url)

# SIGN IN
@method_decorator(check_honeypot, name='dispatch')
class SignInView(FormView):
    form_class = SignInForm
    template_name = 'LandingPage/signin.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        print("LOGIN FORM VALID")
        print("Email:", email)
        print("Password:", password)

        user = authenticate(
            self.request,
            email=email,
            password=password
        )

        if not user:
            form.add_error(
                None,
                'Invalid email or password.'
            )
            return self.form_invalid(form)

        print("Authenticated user:", user.username)
        print("Database role:", user.role)

        login(self.request, user)

        if user.role == 'applicant':
            return redirect(reverse_lazy('applicant-dashboard'))

        if user.role == 'employer':
            return redirect(reverse_lazy('employer-home'))

        return redirect(reverse_lazy('landing-page'))

    def form_invalid(self, form):
        print("LOGIN FORM INVALID")
        print("Form errors:", form.errors)
        print("Non-field errors:", form.non_field_errors())

        return super().form_invalid(form)

# LANDING PAGE
class LandingPageView(TemplateView):
    template_name = 'LandingPage/index.html'