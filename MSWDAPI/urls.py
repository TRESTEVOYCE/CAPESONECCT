from django.urls import path
from .views import SpecialProgramAPI

urlpatterns = [
    path('',SpecialProgramAPI.as_view(),name = 'SpecialProgramAPI'),
]