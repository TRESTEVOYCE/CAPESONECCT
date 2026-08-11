from datetime import __all__

from rest_framework.generics import ListAPIView,RetrieveAPIView
from .serializers import SpecialProgramForEmploymentOfStudentsSerializer,GovernmentInternshipProgramSerializer,TupadBeneficiarySerializer,DisplacedInformalLaborProgramSerializer,CareerGuidanceBeneficiarySerializer
from AdminSide.models import SpecialProgramForEmploymentOfStudents,GovernmentInternshipProgram,TupadBeneficiary,DisplacedInformalLaborProgram,CareerGuidanceBeneficiary
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from AdminSide.permissions import MSWDRolePermission



class SpecialProgramForEmploymentOfStudentsListView(ListAPIView):
    queryset = SpecialProgramForEmploymentOfStudents.objects.all()
    serializer_class = SpecialProgramForEmploymentOfStudentsSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class SpecialProgramForEmploymentOfStudentsDetailView(RetrieveAPIView):
    queryset = SpecialProgramForEmploymentOfStudents.objects.all()
    serializer_class = SpecialProgramForEmploymentOfStudentsSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]



class GovernmentInternshipProgramListView(ListAPIView):
    queryset = GovernmentInternshipProgram.objects.all()
    serializer_class = GovernmentInternshipProgramSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class GovernmentInternshipProgramDetailView(RetrieveAPIView):
    queryset = GovernmentInternshipProgram.objects.all()
    serializer_class = GovernmentInternshipProgramSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]  


class TupadBeneficiaryListView(ListAPIView):
    queryset = TupadBeneficiary.objects.all()
    serializer_class = TupadBeneficiarySerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class TupadBeneficiaryDetailView(RetrieveAPIView):
    queryset = TupadBeneficiary.objects.all()
    serializer_class = TupadBeneficiarySerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]


class DisplacedInformalLaborProgramListView(ListAPIView):
    queryset = DisplacedInformalLaborProgram.objects.all()
    serializer_class = DisplacedInformalLaborProgramSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class DisplacedInformalLaborProgramDetailView(RetrieveAPIView):
    queryset = DisplacedInformalLaborProgram.objects.all()
    serializer_class = DisplacedInformalLaborProgramSerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]


class CareerGuidanceBeneficiaryListView(ListAPIView):
    queryset = CareerGuidanceBeneficiary.objects.all()
    serializer_class = CareerGuidanceBeneficiarySerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class CareerGuidanceBeneficiaryDetailView(RetrieveAPIView):
    queryset = CareerGuidanceBeneficiary.objects.all()
    serializer_class = CareerGuidanceBeneficiarySerializer
    permission_classes = [IsAuthenticated, MSWDRolePermission]




