from django.urls import path
from .views import LandingPageView, SignInView, UserApplicantRegisterView, UserApplicantAccountRegisterView, UserEmployerRegisterView, UserEmployerAccountRegisterView, Register_SelectionView, ActivateAccountView, VerifyEmailView, ForgotPasswordView, PasswordResetSentView, PasswordResetChangeView, PasswordResetSuccessView,TermsAndConditionsView,PrivacyPolicyView, EmployerTermsAndConditionsView, EmployerPrivacyPolicyView

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('login/', SignInView.as_view(), name='signin'),
    path('register/', Register_SelectionView.as_view(), name='register_selection'),
    path('register/jobseeker/', UserApplicantRegisterView.as_view(), name='register_jobseeker'),
    path('register/jobseeker/account/', UserApplicantAccountRegisterView.as_view(), name='applicant-account-register'),
    path('terms-and-conditions/', TermsAndConditionsView.as_view(), name='terms-and-conditions'),
    path('privacy-policy/',  PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('register/employer/', UserEmployerRegisterView.as_view(), name='register_employer'),
    path('register/employer/account/', UserEmployerAccountRegisterView.as_view(), name='employer-account-register'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('password-reset/sent/', PasswordResetSentView.as_view(), name='password_reset_sent'),
    path('password-reset/<uidb64>/<token>/', PasswordResetChangeView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetSuccessView.as_view(), name='password_reset_complete'),
    
    path('employer-privacy-policy/',EmployerPrivacyPolicyView.as_view(),name = 'employer-privacy-policy'),
    path('employer-terms-and-condition/',EmployerTermsAndConditionsView.as_view(),name='employer-terms-and-condition'),
]