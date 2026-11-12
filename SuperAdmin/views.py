
from AdminSide.models import User,AuditLog
from django.views.generic import FormView, TemplateView, ListView,DeleteView,DetailView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from axes.models import AccessAttempt
from .forms import LoginForm,MSWDOAccountCreationForm,PESOAccountCreationForm
from django.contrib import messages
from django.db import transaction
from django.utils.decorators import method_decorator
from honeypot.decorators import check_honeypot
from datetime import timedelta
from django.utils import timezone
from axes.models import AccessFailureLog


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

@method_decorator(check_honeypot, name='dispatch')
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
    model = AccessFailureLog
    template_name = 'SuperAdmin/SuperAdminSystemLogs.html'
    context_object_name = 'logs'
    paginate_by = 25

    def get_queryset(self):
        queryset = AccessFailureLog.objects.all().order_by('-attempt_time')

        time_filter = self.request.GET.get('period', 'all')

        periods = {
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '12h': timedelta(hours=12),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
        }

        if time_filter in periods:
            start_time = timezone.now() - periods[time_filter]
            queryset = queryset.filter(attempt_time__gte=start_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_logs'] = AccessFailureLog.objects.count()
        context['filtered_logs_count'] = context['page_obj'].paginator.count
        context['selected_period'] = self.request.GET.get('period', 'all')

        return context



# ==========================================
# SUPER ADMIN USERS
# ==========================================


class SuperAdminUsers(SuperUserAdmin, ListView):
    model = User
    template_name = 'SuperAdmin/SuperAdminUsers.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all().order_by('username')

        role = self.request.GET.get('role', '').strip()

        valid_roles = ['applicant', 'employer', 'peso', 'mswdo', 'admin']

        if role in valid_roles:
            queryset = queryset.filter(role=role)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_role'] = self.request.GET.get('role', '')
        return context


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



class PESOAccountCreateView(SuperUserAdmin, FormView):
    form_class = PESOAccountCreationForm
    template_name = 'SuperAdmin/create-peso-account.html'
    success_url = reverse_lazy('create_peso_account')

    def form_valid(self, form):
        try:
            peso_user = form.save()

            print("CREATED USER:", peso_user.pk, peso_user.username, peso_user.role)

            AuditLog.objects.create(
                user=self.request.user,
                action=f"Created PESO account: {peso_user.email}",
            )

            messages.success(
                self.request,
                f'PESO account for {peso_user.email} created successfully.'
            )

            return super().form_valid(form)

        except Exception as e:
            print("PESO ACCOUNT CREATION ERROR:", str(e))
            messages.error(self.request, f'Account creation failed: {str(e)}')
            return self.form_invalid(form)

# ==========================================
# DELETE APPLICANT, EMPLOYER, PESO, AND MSWDO ACCOUNTS
# ==========================================

class DeleteAccountView(SuperUserAdmin, DeleteView):
    model = User
    template_name = 'SuperAdmin/confirm_delete_account.html'
    context_object_name = 'account'
    success_url = reverse_lazy('superadmin-users')

    def get_queryset(self):
        """
        Allow deletion only for applicant, employer,
        PESO, and MSWDO accounts.
        """
        return User.objects.filter(
            role__in=['applicant', 'employer', 'peso', 'mswdo']
        )

    def form_valid(self, form):
        account = self.object
        account_email = account.email
        account_role = account.role

        with transaction.atomic():
            response = super().form_valid(form)

            AuditLog.objects.create(
                user=self.request.user,
                action=(
                    f"Deleted {account_role} account: "
                    f"{account_email}"
                ),
            )

        messages.success(
            self.request,
            f'The {account_role.upper()} account '
            f'({account_email}) was deleted successfully.'
        )

        return response

# ==========================================
# VIEW ACCOUNT DETAILS
# ==========================================

class ViewAccountView(SuperUserAdmin, DetailView):
    model = User
    template_name = 'SuperAdmin/view_account.html'
    context_object_name = 'account'

    def get_queryset(self):
        return User.objects.filter(
            role__in=[
                'applicant',
                'employer',
                'peso',
                'mswdo',
                'admin',
            ]
        )