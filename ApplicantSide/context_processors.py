# ApplicantSide/context_processors.py
from AdminSide.models import ApplicantProfile

def applicant_context(request):
    if request.user.is_authenticated and getattr(request.user, 'role', '') == 'applicant':
        profile = ApplicantProfile.objects.filter(user=request.user).first()
        return {'applicant_profile': profile}
    return {}