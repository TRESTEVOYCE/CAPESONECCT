from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

# Create your views here.

def landing_page(request):
    return render(request, 'LandingPage/index.html')

# Alias index to landing_page so views.index works in urls.py
index = landing_page

def signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('user_role')
        
        # Add your authentication or custom model logic here
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing_page') # Redirect to dashboard or landing page
        else:
            return render(request, 'LandingPage/signin.html', {'error': 'Invalid credentials'})

    return render(request, 'LandingPage/signin.html')

def register_selection(request):
    return render(request, 'LandingPage/register_selection.html')