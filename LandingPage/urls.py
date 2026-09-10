from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('signin/', views.signin, name='signin'),
    path('register/', views.register_selection, name='register_selection'),
    path('register/jobseeker/', views.register_jobseeker, name='register_jobseeker'),
    path('register/employer/', views.register_employer, name='register_employer'),
]