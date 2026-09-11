from django.views.generic import ListView,CreateView,UpdateView,DeleteView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from JobMatchingEngine.database import get_job_collection,build_applicant_profile_text
from AdminSide.models import Jobs,ApplicantProfile,AppliedJobs,SavedJobs
from django.contrib.auth.views import LogoutView
from django.db.models import Q
from .forms import ApplicantEducationForm, ApplicantPersonalInfoForm, ApplicantSkillFormSet, ApplicantPreferredJobForm, ApplicantDocumentsForm
from django.urls import reverse_lazy
 
class ApplicantPersonalInfoCreateView(CreateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'applicant_personal_info_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ApplicantEducationCreateView(CreateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'applicant_education_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ApplicantPreferredJobCreateView(CreateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'applicant_preferred_job_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ApplicantDocumentsCreateView(CreateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'applicant_documents_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ApplicantSkillCreateView(CreateView):
    model = ApplicantProfile
    form_class = ApplicantSkillFormSet
    template_name = 'applicant_skill_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
class ApplicantPersonalUpdateInfoView(UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'applicant_personal_info_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)
    
class ApplicantEducationUpdateView(UpdateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'applicant_education_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

class ApplicantSkillUpdateView(UpdateView):
    model = ApplicantProfile
    form_class = ApplicantSkillFormSet
    template_name = 'applicant_skill_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

class ApplicantPreferredJobUpdateView(UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'applicant_preferred_job_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

class ApplicantDocumentsUpdateView(UpdateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'applicant_documents_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

class ApplicantProfileDeleteView(DeleteView):
    model = ApplicantProfile
    success_url = reverse_lazy('login')  # Redirect to the login page after successful deletion

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)


class LogoutView(LogoutView):
    success_url = reverse_lazy('login')
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant
    

class DashBoardView(ListView):
    model = Jobs
    template_name = 'dashboard.html'
    context_object_name = 'matching_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if applicant_profile:
            # Get the applicant profile text for matching
            applicant_profile_text = build_applicant_profile_text(applicant_profile)

            # Get the job collection from ChromaDB
            collection = get_job_collection()

            # Perform a similarity search to find matching jobs
            results = collection.query(
                query_texts=[applicant_profile_text],
                n_results=10  # Number of top matching jobs to retrieve
            )

            # Extract job UUIDs from the results
            job_uuids = [result['metadata']['job_uuid'] for result in results['results'][0]['matches']]

            # Retrieve the matching job objects from the database
            matching_jobs = Jobs.objects.filter(uuid__in=job_uuids)

            context['matching_jobs'] = matching_jobs
        else:
            context['matching_jobs'] = []

        return context

class JobListView(ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        return Jobs.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if applicant_profile:
            # Get the applicant profile text for matching
            applicant_profile_text = build_applicant_profile_text(applicant_profile)

            # Get the job collection from ChromaDB
            collection = get_job_collection()

            # Perform a similarity search to find matching jobs
            results = collection.query(
                query_texts=[applicant_profile_text]
            )

            # Extract job UUIDs from the results
            job_uuids = [result['metadata']['job_uuid'] for result in results['results'][0]['matches']]

            # Retrieve the matching job objects from the database
            matching_jobs = Jobs.objects.filter(uuid__in=job_uuids)

            context['matching_jobs'] = matching_jobs
        else:
            context['matching_jobs'] = []
        return context

class JobDetailsView(DetailView):
    model = Jobs
    template_name = 'job_details.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_uuid = self.kwargs.get('uuid')
        job = Jobs.objects.filter(uuid=job_uuid).first()
        context['job'] = job
        return context

class SortJobView(ListView):
    model = Jobs
    context_object_name = 'matching_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        sort_by = self.request.GET.get('sort_by', 'date_posted')  # Default sorting by date_posted
        if sort_by == 'date_posted':
            return Jobs.objects.all().order_by('-date_posted')
        elif sort_by == 'salary':
            return Jobs.objects.all().order_by('-salary')
        else:
            return Jobs.objects.all()  # Default case if no valid sort option is provided


class AppliedJobsListView(ListView):
    model = AppliedJobs
    template_name = 'applied_jobs.html'
    context_object_name = 'applied_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        return AppliedJobs.objects.filter(applicant=self.request.user)


class SavedJobsListView(ListView):
    model = SavedJobs
    template_name = 'saved_jobs.html'
    context_object_name = 'saved_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        return SavedJobs.objects.filter(applicant=self.request.user)

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if applicant_profile:
            return applicant_profile.saved_jobs.all()
        return Jobs.objects.none()

class SearchJobView(ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_applicant

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Jobs.objects.filter(
                Q(job_title__icontains=query) |
                Q(job_description__icontains=query) |
                Q(employer__business_name__icontains=query)
            )
        else:
            return Jobs.objects.all()