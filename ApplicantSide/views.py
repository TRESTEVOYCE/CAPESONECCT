from django.views.generic import TemplateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from AdminSide.models import Jobs
from JobMatchingEngine.database import get_job_collection,build_applicant_profile_text
from AdminSide.models import Jobs,ApplicantProfile


#recomendations views for the applicant dashboard
class RecommendationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'feed.html'
    model = Jobs
    context_object_name = 'jobs'

    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'applicantprofile')


    def get_queryset(self):
        applicant = ApplicantProfile.objects.get(user=self.request.user)

       #Convert the applicant profile into searchable text

        applicant_profile_text = build_applicant_profile_text(applicant)

        collection = get_job_collection()

        results = collection.query(
            query_texts=[applicant_profile_text],
            n_results=10
        )

        job_uuids = [result['id'] for result in results['results'][0]['matches']]

        return Jobs.objects.filter(uuid__in=job_uuids)

    