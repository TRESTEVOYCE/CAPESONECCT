from django.contrib import admin
from . models import User, EmployerProfile, PESOActivities, AuditLog, Jobs, ApplicantProfile, ApplicantSkills, AppliedJobs, OfferedJobs

# Register your models here.

admin.site.register(User)
admin.site.register(EmployerProfile)
admin.site.register(PESOActivities)
admin.site.register(AuditLog)
admin.site.register(Jobs)
admin.site.register(ApplicantProfile)
admin.site.register(ApplicantSkills)
admin.site.register(AppliedJobs)
admin.site.register(OfferedJobs)
