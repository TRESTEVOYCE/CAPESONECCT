from rest_framework import serializers
from AdminSide.models import SpecialProgramForEmploymentOfStudents,GovernmentInternshipProgram,TupadBeneficiary,DisplacedInformalLaborProgram,CareerGuidanceBeneficiary
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

    
class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"



class SpecialProgramForEmploymentOfStudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialProgramForEmploymentOfStudents
        fields = '__all__'

class GovernmentInternshipProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentInternshipProgram
        fields = '__all__'

class TupadBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TupadBeneficiary
        fields = '__all__'

class DisplacedInformalLaborProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplacedInformalLaborProgram
        fields = '__all__'

class CareerGuidanceBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerGuidanceBeneficiary
        fields = '__all__'