from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from AdminSide.models import (
    SpecialProgramForEmploymentOfStudents,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    CareerGuidanceBeneficiary,
)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that uses email as the login field.
    """

    username_field = "email"


class ReadOnlyModelSerializer(serializers.ModelSerializer):
    """
    Base serializer that makes every model field read-only.

    API clients can retrieve beneficiary information but cannot
    create or update records through these serializers.
    """

    def get_fields(self):
        fields = super().get_fields()

        for field in fields.values():
            field.read_only = True

        return fields


class SpecialProgramForEmploymentOfStudentsSerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer for Special Program for Employment
    of Students (SPES) beneficiaries.
    """

    class Meta:
        model = SpecialProgramForEmploymentOfStudents
        fields = "__all__"


class GovernmentInternshipProgramSerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer for Government Internship Program (GIP)
    beneficiaries.
    """

    class Meta:
        model = GovernmentInternshipProgram
        fields = "__all__"


class TupadBeneficiarySerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer for TUPAD beneficiaries.
    """

    class Meta:
        model = TupadBeneficiary
        fields = "__all__"


class DisplacedInformalLaborProgramSerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer for Displaced Informal Labor Program (DILP)
    beneficiaries.
    """

    class Meta:
        model = DisplacedInformalLaborProgram
        fields = "__all__"


class CareerGuidanceBeneficiarySerializer(ReadOnlyModelSerializer):
    """
    Read-only serializer for Career Guidance beneficiaries.
    """

    class Meta:
        model = CareerGuidanceBeneficiary
        fields = "__all__"
