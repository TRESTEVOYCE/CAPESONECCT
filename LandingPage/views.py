from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.generic import TemplateView, View
from AdminSide.models import EmployerProfile 

class LandingPageView(TemplateView):
    template_name = 'LandingPage/index.html'

class SignInView(View):
    template_name = 'LandingPage/signin.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('user_role')
        
        # Try authenticating directly with the input (supports username or email lookup fallback)
        user = authenticate(request, username=email_or_username, password=password)
        if user is None:
            try:
                matched_user = User.objects.get(email=email_or_username)
                user = authenticate(request, username=matched_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            
            # If employer role is selected or profile exists, route to EmployerSide/home ('home')
            if role == 'employer' or hasattr(user, 'employer_profile'):
                return redirect('home')
            
            return redirect('landing_page')
        else:
            return render(request, self.template_name, {'error': 'Invalid credentials'})

class RegisterSelectionView(TemplateView):
    template_name = 'LandingPage/register_selection.html'

class RegisterJobseekerView(View):
    template_name = 'LandingPage/register_jobseeker.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return redirect('signin')

class RegisterEmployerView(View):
    template_name = 'LandingPage/register_employer.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        email = request.POST.get('rep_email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Server-side validation for matching passwords
        if password != confirm_password:
            return render(request, self.template_name, {'error': 'Passwords do not match.'})

        # Check for duplicate credentials
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            return render(request, self.template_name, {'error': 'Username or email already exists.'})

        # 1. Create the base Django User account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('rep_full_name', '')
        )

        if hasattr(user, 'role'):
            user.role = 'employer'
            user.save()

        # 2. Create and link the EmployerProfile using the multi-step form data
        EmployerProfile.objects.create(
            user=user,
            company_name=request.POST.get('company_name'),
            trade_name=request.POST.get('trade_name'),
            employer_type=request.POST.get('employer_type'),
            industry_sector=request.POST.get('industry_sector'),
            street_address=request.POST.get('street_address'),
            municipality=request.POST.get('municipality'),
            province=request.POST.get('province'),
            tin_number=request.POST.get('tin_number'),
            rep_full_name=request.POST.get('rep_full_name'),
            rep_designation=request.POST.get('rep_designation'),
            company_phone=request.POST.get('company_phone'),
            company_landline=request.POST.get('company_landline'),
            company_website=request.POST.get('company_website'),
            business_permit=request.FILES.get('business_permit'),
        )

        # 3. Redirect to the sign-in page after successful registration
        return redirect('signin')