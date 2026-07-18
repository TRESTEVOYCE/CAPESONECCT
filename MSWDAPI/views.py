from rest_framework.generics import ListAPIView,RetrieveAPIView
from .serializers import SpecialProgramSerializer
from AdminSide.models import SpecialProgramBeneficiaries
from rest_framework.permissions import IsAuthenticated


class SpecialProgramAPI(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = SpecialProgramBeneficiaries.objects.all
    serializer_class = SpecialProgramSerializer

