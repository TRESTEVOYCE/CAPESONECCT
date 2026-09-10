from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('signin/', views.signin, name='signin'),
    path('register/', views.register_selection, name='register_selection'),
]