# capes_admin/urls.py
from django.urls import path
from .views import DashboardView, JobPostingsListView

app_name = 'AdminSide'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('jobs/', JobPostingsListView.as_view(), name='job_postings_list'),
]