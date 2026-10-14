
from AdminSide.models import User, AuditLog
from django.views.generic import (
    FormView, TemplateView, ListView, UpdateView, DeleteView
)
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from axes.models import AccessAttempt

from .forms import (
    LoginForm,
    MSWDOAccountCreationForm,
    PESOAccountCreationForm,
    StaffAccountUpdateForm,
)
from django.utils import timezone
from django.urls import reverse
from .forms import SuperAdminPasswordConfirmForm
from django.shortcuts import redirect, get_object_or_404


# SUPER ADMIN ACCESS
class SuperUserAdmin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('super_login')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'admin'
        )

    def handle_no_permission(self):
        return redirect('signin')




class StaffEditPasswordRequiredMixin:
    password_action = None

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        action = self.password_action

        if action not in ("edit", "delete") or pk is None:
            return redirect("superadmin-users")

        session_key = f"staff_action_verified_{pk}_{action}"
        verified_at = request.session.get(session_key)

        try:
            elapsed = timezone.now().timestamp() - float(verified_at)
        except (TypeError, ValueError):
            elapsed = 301

        if elapsed < 0 or elapsed > 300:
            request.session.pop(session_key, None)
            return redirect(
                f"{reverse_lazy('staff-account-password-confirm', kwargs={'pk': pk})}?action={action}"
            )

        # Keep authorization during GET so the edit or confirmation
        # page can load. Consume it on POST.
        if request.method == "POST":
            request.session.pop(session_key, None)

        return super().dispatch(request, *args, **kwargs)




# LOGIN
class SuperAdminLoginView(FormView):
    form_class = LoginForm
    template_name = 'SuperAdmin/super_admin_login.html'
    success_url = reverse_lazy('superadmin-dashboard')

    def form_valid(self, form):
        user = authenticate(
            self.request,
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password']
        )

        if user is None:
            form.add_error(None, 'Invalid email or password.')
            return self.form_invalid(form)

        if user.role != 'admin':
            form.add_error(None, 'You are not authorized to access this page.')
            return self.form_invalid(form)

        login(self.request, user)
        return redirect('superadmin-dashboard')


# LOGOUT
class SuperAdminLogoutView(SuperUserAdmin, LogoutView):
    next_page = reverse_lazy('super_login')


# DASHBOARD
class SuperAdminDashboard(SuperUserAdmin, TemplateView):
    template_name = 'SuperAdmin/SuperAdminDashboard.html'


# SYSTEM LOGS
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


# MANAGE USERS
class SuperAdminUsers(SuperUserAdmin, ListView):
    model = User
    template_name = 'SuperAdmin/SuperAdminUsers.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        return User.objects.filter(
            role__in=['applicant', 'employer', 'mswdo', 'peso']
        ).order_by('role', 'email')


# CREATE MSWDO ACCOUNT
class MSWDOAccountCreateView(SuperUserAdmin, FormView):
    form_class = MSWDOAccountCreationForm
    template_name = 'SuperAdmin/create_mswdo_account.html'
    success_url = reverse_lazy('create_mswdo_account')

    def form_valid(self, form):
        user = form.save()
        AuditLog.objects.create(
            user=self.request.user,
            action=f"Created MSWDO account: {user.email}"
        )
        messages.success(
            self.request, f'MSWDO account for {user.email} created successfully.'
        )
        return super().form_valid(form)


# CREATE PESO ACCOUNT
class PESOAccountCreationView(SuperUserAdmin, FormView):
    form_class = PESOAccountCreationForm
    template_name = 'SuperAdmin/create_PESO_account.html'
    success_url = reverse_lazy('peso_account_creation')

    def form_valid(self, form):
        user = form.save()
        AuditLog.objects.create(
            user=self.request.user,
            action=f"Created PESO account: {user.email}"
        )
        messages.success(
            self.request, f'PESO account for {user.email} created successfully.'
        )
        return super().form_valid(form)


# UPDATE MSWDO / PESO ACCOUNT

class StaffAccountUpdateView(
    SuperUserAdmin,
    StaffEditPasswordRequiredMixin,
    UpdateView,
):
    model = User
    form_class = StaffAccountUpdateForm
    template_name = "SuperAdmin/update_staff_account.html"
    success_url = reverse_lazy("superadmin-users")
    password_action = "edit"

    def get_queryset(self):
        return User.objects.filter(role__in=["mswdo", "peso"])

    def form_valid(self, form):
        response = super().form_valid(form)

        AuditLog.objects.create(
            user=self.request.user,
            action=f"Updated staff account: {self.object.email}",
        )

        messages.success(
            self.request,
            "Staff account updated successfully.",
        )
        return response



# DELETE MSWDO / PESO ACCOUNT
class StaffAccountDeleteView(
    SuperUserAdmin, StaffEditPasswordRequiredMixin, DeleteView
):
    password_action = "delete"
    model = User
    template_name = "SuperAdmin/delete_staff_account.html"
    success_url = reverse_lazy("superadmin-users")

    def get_queryset(self):
        return User.objects.filter(
            role__in=["applicant", "employer", "mswdo", "peso"]
        )

    def form_valid(self, form):
        email = self.object.email
        username = self.object.username
        role = self.object.role

        AuditLog.objects.create(
            user=self.request.user,
            action=f"Deleted {role.upper()} account: {email} (username: {username})"
        )

        messages.success(
            self.request,
            f"{role.upper()} account for {email} deleted successfully."
        )

        return super().form_valid(form)




class StaffAccountPasswordConfirmView(SuperUserAdmin, FormView):
    template_name = "SuperAdmin/confirm_staff_edit_password.html"
    form_class = SuperAdminPasswordConfirmForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = (
            self.request.POST.get("action")
            or self.request.GET.get("action", "")
        )
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Incorrect password.")
        return super().form_invalid(form)

    def form_valid(self, form):
        action = self.request.POST.get("action", "").strip()
        pk = self.kwargs["pk"]

        allowed_actions = {
            "edit": ["mswdo", "peso"],
            "delete": ["applicant", "employer", "mswdo", "peso"],
        }

        if action not in allowed_actions:
            messages.error(self.request, "Invalid account action.")
            return redirect("superadmin-users")

        target = get_object_or_404(
            User,
            pk=pk,
            role__in=allowed_actions[action],
        )

        self.request.session[
            f"staff_action_verified_{pk}_{action}"
        ] = timezone.now().timestamp()

        if action == "delete":
            return redirect("staff-account-delete", pk=target.pk)

        return redirect("staff-account-update", pk=target.pk)
