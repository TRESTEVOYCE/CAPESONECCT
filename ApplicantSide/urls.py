from django.urls import path
from .views import ApplicantPersonalInfoCreateView, ApplicantEducationCreateView, ApplicantPreferredJobCreateView, ApplicantDocumentsCreateView, ApplicantSkillCreateView, ApplicantPersonalUpdateInfoView, ApplicantEducationUpdateView, ApplicantSkillUpdateView, ApplicantPreferredJobUpdateView, ApplicantDocumentsUpdateView, ApplicantProfileDeleteView, LogoutView, DashBoardView, JobListView, JobDetailsView, SortJobView, AppliedJobsListView, SavedJobsListView, SearchJobView


urlpatterns = [
    path('personal_info/', ApplicantPersonalInfoCreateView.as_view(), name='personal_info'),
    path('education/', ApplicantEducationCreateView.as_view(), name='education'),
    path('preferred_job/', ApplicantPreferredJobCreateView.as_view(), name='preferred_job'),
    path('documents/', ApplicantDocumentsCreateView.as_view(), name='documents'),
    path('skills/', ApplicantSkillCreateView.as_view(), name='skills'),

    path('personal_info/update/', ApplicantPersonalUpdateInfoView.as_view(), name='personal_info_update'),
    path('education/update/', ApplicantEducationUpdateView.as_view(), name='education_update'),
    path('skills/update/', ApplicantSkillUpdateView.as_view(), name='skills_update'),
    path('preferred_job/update/', ApplicantPreferredJobUpdateView.as_view(), name='preferred_job_update'),
    path('documents/update/', ApplicantDocumentsUpdateView.as_view(), name='documents_update'),

    path('profile/delete/', ApplicantProfileDeleteView.as_view(), name='profile_delete'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashBoardView.as_view(), name='dashboard'),

    path('jobs/', JobListView.as_view(), name='job_list'),
    path('jobs/sort/', SortJobView.as_view(), name='sort_jobs'),
    path('search_jobs/', SearchJobView.as_view(), name='search_jobs'),
    path('jobs/<int:pk>/', JobDetailsView.as_view(), name='job_details'),

    path('applied_jobs/', AppliedJobsListView.as_view(), name='applied_jobs'),
    path('saved_jobs/', SavedJobsListView.as_view(), name='saved_jobs'),
]