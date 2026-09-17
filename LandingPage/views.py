from django.views.generic import CreateView, FormView, TemplateView
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.urls import reverse_lazy

from AdminSide.models import EmployerProfile, User
from .forms import UserRegisterForm, SignInForm


class Register_SelectionView(TemplateView):
    template_name = 'LandingPage/register_selection.html'

class UserRegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    user_role = None

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.role = self.user_role
        self.object.save()

        return redirect(self.success_url)


class UserApplicantRegisterView(UserRegisterView):
    template_name = 'LandingPage/register_jobseeker.html'
    user_role = 'applicant'
    success_url = reverse_lazy('applicant-dashboard') 

class UserEmployerRegisterView(UserRegisterView):
    template_name = 'LandingPage/register_employer.html'
    user_role = 'employer'
    success_url = reverse_lazy('employer-home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.role = self.user_role
        self.object.save()
        EmployerProfile.objects.get_or_create(user=self.object)
        return redirect(self.success_url)


class SignInView(FormView):
    form_class = SignInForm
    template_name = 'LandingPage/signin.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        print("LOGIN FORM VALID")
        print("Email:", email)
        print("Password:", password)

        user = authenticate(self.request, email=email, password=password)
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

class LandingPageView(TemplateView):
    template_name = 'LandingPage/index.html'
