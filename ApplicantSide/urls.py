from django.urls import path
from .views import ApplicantPersonalInfoView, ApplicantAddressView, ApplicantEducationView, ApplicantTrainingView, ApplicantPreferredJobView, ApplicantWorkExperienceView, ApplicantSkillsView, ApplicantDocumentsView, ApplicantProfileDeleteView, ApplicantReverificationAppealView, ApplicantMarkAllNotificationsReadView, ApplicantMarkNotificationReadView, ApplicantDeleteNotificationView, ApplicantNotificationHeaderApiView, ApplicantNotificationListView, LogoutView, DashBoardView, JobListView, JobDetailsView, SortJobView, AppliedJobsListView, SavedJobsListView, SearchJobView, ApplyJobView, SaveJobView, EditProfilePictureView, UnsaveJobView, ViewProfileView,MyProfileView, UpdateUsernameView,SettingsView, SettingsView, update_email_view, send_email_otp,send_password_otp_view, verify_password_otp_view, SecurePasswordChangeView, UpdateUsernameView, HelpPageView, send_applicant_support_message_api



urlpatterns = [
    path('notifications/', ApplicantNotificationListView.as_view(), name='applicant-notifications'),
    path('notifications/api/header/', ApplicantNotificationHeaderApiView.as_view(), name='applicant-notifications-header'),
    path('notifications/<int:notification_id>/read/', ApplicantMarkNotificationReadView.as_view(), name='applicant-notification-read'),
    path('notifications/read-all/', ApplicantMarkAllNotificationsReadView.as_view(), name='applicant-notifications-read-all'),
    path('notifications/<int:notification_id>/delete/', ApplicantDeleteNotificationView.as_view(), name='applicant-notification-delete'),
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
    path('appeal/reverification/', ApplicantReverificationAppealView.as_view(), name='applicant-reverification-appeal'),

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

    
    # SETTINGS & SECURITY ROUTES 
    path('settings/', SettingsView.as_view(), name='settings'),
    path('update_username/', UpdateUsernameView.as_view(), name='update-username'),
    path('update_email/', update_email_view, name='update-email'),
    path('send_email_otp/', send_email_otp, name='send-email-otp'),
    
    path('send_password_otp/', send_password_otp_view, name='send-password-otp'),
    path('verify_password_otp/', verify_password_otp_view, name='verify-password-otp'),
    path('update_password/', SecurePasswordChangeView.as_view(), name='update-password'),
    
    # NEED / HELP
    path('help/', HelpPageView.as_view(), name='applicant-help'),
    path('help/send-support-message/', send_applicant_support_message_api, name='applicant-send-support-message'),
]
