from rest_framework import serializers
from AdminSide.models import SpecialProgramBeneficiaries


class SpecialProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialProgramBeneficiaries
        fields = ['uuid','first_name','middle_name','last_name','sex','date_of_birth','phone_number','email','barangay','municipality','province','region','zip_code','daily_salary','start_date','end_date','type_of_program','is_done']