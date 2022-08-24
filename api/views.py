from rest_framework.views import APIView
from rest_framework.response import Response
import concurrent.futures
import json


# Create your views here.
class getPrice(APIView):
    def get(self, request):
        return Response({"message": "Get card price"})

class getBulkPrice(APIView):
    def post(self, request):
        return Response({"message": "Get card bulk price"})