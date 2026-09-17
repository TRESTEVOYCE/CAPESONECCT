from django.urls import path
from .views import LandingPageView, SignInView, UserApplicantRegisterView, UserEmployerRegisterView,Register_SelectionView
urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('login/', SignInView.as_view(), name='signin'),
    path('register/', Register_SelectionView.as_view(), name='register_selection'),
    path('register/jobseeker/', UserApplicantRegisterView.as_view(), name='register_jobseeker'),
    path('register/employer/', UserEmployerRegisterView.as_view(), name='register_employer'),
]