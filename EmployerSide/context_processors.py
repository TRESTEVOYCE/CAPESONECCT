# EmployerSide/context_processors.py
from AdminSide.models import EmployerProfile

def employer_context(request):
    if request.user.is_authenticated and getattr(request.user, 'role', '') == 'employer':
        profile = EmployerProfile.objects.filter(user=request.user).first()
        return {'employer_profile': profile}
    return {}