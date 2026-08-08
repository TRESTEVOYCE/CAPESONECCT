from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from .models import GovernmentInternshipProgram, SpecialProgramForEmploymentOfStudents
from .service import generate_complete_peso_matrix
from .views import EnrollBeneficiaryView, SpecialProgramsListView


class EnrollBeneficiaryViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = EnrollBeneficiaryView()

    def test_get_instance_uses_the_configured_program_model(self):
        beneficiary = SpecialProgramForEmploymentOfStudents.objects.create(
            first_name='Ana',
            last_name='Rivera',
            sex='F',
            date_of_birth='2000-01-01',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1000.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
        )

        request = self.factory.get('/special-programs/enroll/', {'edit': beneficiary.uuid, 'program': 'spes'})
        instance = self.view.get_instance(request, {'model': SpecialProgramForEmploymentOfStudents})

        self.assertEqual(instance, beneficiary)

    def test_special_program_list_view_handles_search_query(self):
        request = self.factory.get('/special-programs/', {'program': 'spes', 'search': 'Ana'})
        response = SpecialProgramsListView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_enroll_post_preserves_municipality_and_barangay_from_current_form_fields(self):
        client = Client()
        response = client.post('/special-programs/enroll/?program=spes', {
            'first_name': 'Ana',
            'middle_name': '',
            'last_name': 'Rivera',
            'sex': 'F',
            'date_of_birth': '2000-01-01',
            'phone_number': '09123456789',
            'barangay': 'Poblacion',
            'municipality': 'Carigara',
            'province': 'Leyte',
            'region': 'VIII',
            'zip_code': '6529',
            'daily_salary': '1000',
            'start_date': '2024-01-01',
            'end_date': '2024-02-01',
            'education_level': 'college',
        })

        self.assertEqual(response.status_code, 302)
        beneficiary = SpecialProgramForEmploymentOfStudents.objects.get(first_name='Ana')
        self.assertEqual(beneficiary.municipality, 'Carigara')
        self.assertEqual(beneficiary.barangay, 'Poblacion')

    def test_generate_complete_peso_matrix_counts_special_program_data(self):
        SpecialProgramForEmploymentOfStudents.objects.create(
            first_name='Ana',
            last_name='Rivera',
            sex='F',
            date_of_birth='2000-01-01',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1000.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
            has_graduated=True,
            has_nc_certification=True,
            is_absorbed_by_employer=True,
        )

        GovernmentInternshipProgram.objects.create(
            first_name='Luis',
            last_name='Santos',
            sex='F',
            date_of_birth='1999-02-02',
            phone_number='09123456790',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1200.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
            has_nc_certification=True,
            is_absorbed_by_agency=True,
        )

        current_year = timezone.now().year
        current_month = timezone.now().month
        metrics = generate_complete_peso_matrix(current_year, current_month)

        self.assertEqual(metrics['spes_college'], 1)
        self.assertEqual(metrics['spes_graduates'], 1)
        self.assertEqual(metrics['spes_nc'], 1)
        self.assertEqual(metrics['spes_absorbed'], 1)
        self.assertEqual(metrics['gip_total'], 1)
        self.assertEqual(metrics['gip_female'], 1)
        self.assertEqual(metrics['gip_graduates_nc'], 1)
        self.assertEqual(metrics['gip_absorbed'], 1)
