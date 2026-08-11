from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission




#Base Role for all other roles to inherit from this
class RequiredRoleMixin(UserPassesTestMixin):

    required_role = None

    def test_func(self):
        return self.request.user.role == self.required_role

    def handle_no_permission(self):
        return redirect('home')

    
#class used to check if it is the role needed. Plug it in like a battery
class EmployerRoleMixin(RequiredRoleMixin):
    required_role = 'employer'

class AdminRoleMixin(RequiredRoleMixin):
    required_role = 'admin'

class ApplicantRoleMixin(RequiredRoleMixin):
    required_role = 'applicant'

class PesoRoleMixin(RequiredRoleMixin):
    required_role = 'peso'


#Permission classes for DRF API views
class MSWDRolePermission(BasePermission):

    message = 'MSWDO ADMIN AND PESO ROLE IS REQUIRED TO ACCESS THE RESOURCE'

    def has_permission(self, request, view):
        return request.user.role in ['mswdo', 'admin', 'peso']