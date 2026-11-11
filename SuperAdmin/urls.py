from django.urls import path
from .views import SuperAdminLoginView, SuperAdminLogoutView, SuperAdminDashboard,SuperAdminSystemLogs, SuperAdminUsers, MSWDOAccountCreateView,PESOAccountCreateView, DeleteAccountView, ViewAccountView

urlpatterns = [
    path('', SuperAdminLoginView.as_view(), name='super_login'),
    path('SuperLogout/', SuperAdminLogoutView.as_view(), name='super_logout'),
    path('SuperDashboard/', SuperAdminDashboard.as_view(), name='superadmin-dashboard'),
    path('SuperSystemLogs/', SuperAdminSystemLogs.as_view(), name='superadmin-system-logs'),
    path('SuperUsers/', SuperAdminUsers.as_view(), name='superadmin-users'),
    path('Create-MSWDO-Account/', MSWDOAccountCreateView.as_view(), name='create_mswdo_account'),
    path('create-peso-account/', PESOAccountCreateView.as_view(), name='create_peso_account'),
    path('view-account/<int:pk>/', ViewAccountView.as_view(), name='view_account'),
    path('delete-account/<int:pk>/', DeleteAccountView.as_view(), name='delete_account'),
]
