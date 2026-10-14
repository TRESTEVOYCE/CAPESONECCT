from django.urls import path
from .views import SuperAdminLoginView, SuperAdminLogoutView, SuperAdminDashboard, SuperAdminSystemLogs,SuperAdminUsers,MSWDOAccountCreateView,PESOAccountCreationView,StaffAccountDeleteView,StaffAccountUpdateView,StaffAccountPasswordConfirmView


urlpatterns = [
    path('', SuperAdminLoginView.as_view(), name='super_login'),
    path('SuperLogout/', SuperAdminLogoutView.as_view(), name='super_logout'),
    path('SuperDashboard/', SuperAdminDashboard.as_view(), name='superadmin-dashboard'),
    path('SuperSystemLogs/', SuperAdminSystemLogs.as_view(), name='superadmin-system-logs'),
    path('SuperUsers/', SuperAdminUsers.as_view(), name='superadmin-users'),
    path('Create-MSWDO-Account/', MSWDOAccountCreateView.as_view(), name='create_mswdo_account'),
    path('peso-account-creation/',PESOAccountCreationView.as_view(),name='peso_account_creation'),
    path('staff-account/<int:pk>/edit/', StaffAccountUpdateView.as_view(), name='staff-account-update'),
    path('staff-account/<int:pk>/delete/', StaffAccountDeleteView.as_view(), name='staff-account-delete'),  
    path('staff-account/<int:pk>/verify-password/', StaffAccountPasswordConfirmView.as_view(), name='staff-account-password-confirm'),
]
