from AdminSide.models import ApplicantProfile


def applicant_profile(request):
    profile = None

    if request.user.is_authenticated and request.user.role == 'applicant':
        profile = ApplicantProfile.objects.filter(
            user=request.user
        ).first()

    return {
        'applicant_profile': profile
    }