
from AdminSide.models import User,AuditLog
from django.views.generic import FormView, TemplateView, ListView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from axes.models import AccessAttempt
from .forms import LoginForm,MSWDOAccountCreationForm


# ==========================================
# SUPER ADMIN ACCESS CONTROL
# ==========================================

class SuperUserAdmin(LoginRequiredMixin, UserPassesTestMixin):

    login_url = reverse_lazy('superadmin_login')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'admin'
        )

    def handle_no_permission(self):
        return redirect('signin')


# ==========================================
# SUPER ADMIN LOGIN
# ==========================================

class SuperAdminLoginView(FormView):
    form_class = LoginForm
    template_name = 'SuperAdmin/super_admin_login.html'
    success_url = reverse_lazy('superadmin-dashboard')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(
            self.request,
            email=email,
            password=password
        )

        if user is None:
            form.add_error(None, 'Invalid email or password.')
            return self.form_invalid(form)

        if user.role != 'admin':
            form.add_error(
                None,
                'You are not authorized to access this page.'
            )
            return self.form_invalid(form)

        login(self.request, user)

        return redirect('superadmin-dashboard')


# ==========================================
# SUPER ADMIN LOGOUT
# ==========================================

class SuperAdminLogoutView(SuperUserAdmin, LogoutView):
    next_page = reverse_lazy('super_login')


# ==========================================
# SUPER ADMIN DASHBOARD
# ==========================================

class SuperAdminDashboard(SuperUserAdmin, TemplateView):
    template_name = 'SuperAdmin/SuperAdminDashboard.html'


# ==========================================
# SUPER ADMIN SYSTEM LOGS - DJANGO AXES
# ==========================================


class SuperAdminSystemLogs(SuperUserAdmin, ListView):
    model = AccessAttempt
    template_name = 'SuperAdmin/SuperAdminSystemLogs.html'
    context_object_name = 'logs'
    paginate_by = 25

    def get_queryset(self):
        return AccessAttempt.objects.order_by('-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_logs'] = AccessAttempt.objects.count()
        context['axes_fields'] = [
            field.name for field in AccessAttempt._meta.fields
        ]
        return context



class SuperAdminUsers(SuperUserAdmin, ListView):
    model = User
    template_name = 'SuperAdmin/SuperAdminUsers.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        return User.objects.filter(
            role__in=['applicant', 'employer']
        ).order_by('role', 'email')

# ==========================================
# CREATE MSWDO ACCOUNT
# ==========================================

class MSWDOAccountCreateView(SuperUserAdmin, FormView):
    form_class = MSWDOAccountCreationForm
    template_name = 'SuperAdmin/create_mswdo_account.html'
    success_url = reverse_lazy('create_mswdo_account')

    def form_valid(self, form):
        mswdo_user = form.save()

        AuditLog.objects.create(
            user=self.request.user,
            action=f"Created MSWDO account: {mswdo_user.email}",
        )

        from django.contrib import messages
        messages.success(
            self.request,
            f'MSWDO account for {mswdo_user.email} created successfully.'
        )

        return super().form_valid(form)




