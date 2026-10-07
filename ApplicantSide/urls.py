from django.urls import path
from .views import ApplicantPersonalInfoView, ApplicantAddressView, ApplicantEducationView, ApplicantTrainingView, ApplicantPreferredJobView, ApplicantWorkExperienceView, ApplicantSkillsView, ApplicantDocumentsView, ApplicantProfileDeleteView, LogoutView, DashBoardView, JobListView, JobDetailsView, SortJobView, AppliedJobsListView, SavedJobsListView, SearchJobView, ApplyJobView, SaveJobView, EditProfilePictureView, UnsaveJobView, ViewProfileView,MyProfileView


urlpatterns = [
    path('', DashBoardView.as_view(), name='applicant-dashboard'),
    path('my_profile/', MyProfileView.as_view(), name='my_profile'),
    path('personal_info/', ApplicantPersonalInfoView.as_view(), name='personal_info'),
    path('address/', ApplicantAddressView.as_view(), name='applicant-address'),
    path('education/', ApplicantEducationView.as_view(), name='applicant-education'),
    path('training/', ApplicantTrainingView.as_view(), name='applicant-training'),
    path('preferred_job/', ApplicantPreferredJobView.as_view(), name='applicant-preferred-job'),
    path('work_experience/', ApplicantWorkExperienceView.as_view(), name='applicant-work-experience'),
    path('skills/', ApplicantSkillsView.as_view(), name='applicant-skills'),
    path('documents/', ApplicantDocumentsView.as_view(), name='applicant-documents'),

    path('profile/delete/', ApplicantProfileDeleteView.as_view(), name='profile_delete'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('jobs/', JobListView.as_view(), name='job_list'),
    path('jobs/sort/', SortJobView.as_view(), name='sort_jobs'),
    path('search_jobs/', SearchJobView.as_view(), name='search_jobs'),
    path('jobs/<int:pk>/', JobDetailsView.as_view(), name='job_details'),
    path('jobs/<int:pk>/apply/', ApplyJobView.as_view(), name='apply-for-job'),
    path('jobs/<int:pk>/save/', SaveJobView.as_view(), name='save_job'),
    path('saved-jobs/', SavedJobsListView.as_view(), name='saved_jobs'),
    path('saved-jobs/<int:pk>/unsave/', UnsaveJobView.as_view(), name='unsave_job'),

    path('applied_jobs/', AppliedJobsListView.as_view(), name='applied_jobs'),
    path('personal_info/edit_profile_picture/', EditProfilePictureView.as_view(), name='edit_profile_picture'),
    path('personal_info/profile/', ViewProfileView.as_view(), name='view_profile'),
]