from django.urls import path
from .views import LandingPageView, SignInView, RegisterSelectionView, RegisterEmployerView, RegisterJobseekerView

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('register/', RegisterSelectionView.as_view(), name='register_selection'),
    path('register/jobseeker/', RegisterJobseekerView.as_view(), name='register_jobseeker'),
    path('register/employer/', RegisterEmployerView.as_view(), name='register_employer'),
]