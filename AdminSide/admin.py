from django.contrib import admin
from . models import User, EmployerProfile, PESOActivities, AuditLog, Jobs, ApplicantProfile, ApplicantSkills, AppliedJobs, OfferedJobs, GovernmentInternshipProgram, TupadBeneficiary, DisplacedInformalLaborProgram, SpecialProgramForEmploymentOfStudents

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
admin.site.register(GovernmentInternshipProgram)
admin.site.register(TupadBeneficiary)
admin.site.register(DisplacedInformalLaborProgram)
admin.site.register(SpecialProgramForEmploymentOfStudents)
admin.site.register(PESOActivities)
admin.site.register(AuditLog)
