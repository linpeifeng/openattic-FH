# -*- coding: utf-8 -*-

import exec_diskroam
from alerts.serializers import *
from rest_framework import generics
from rest.utilities import get_request_data
from django.http import HttpResponse
from rest_framework.permissions import IsSuperAdminUser
# Create your views here.

class Alert_List(generics.ListCreateAPIView):
    queryset = Alert_Info.objects.all()
    serializer_class = AlertSerializers

class Alert_ViewInfo(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alert_Info.objects.all()
    serializer_class = AlertSerializers

class Snmp_List(generics.ListCreateAPIView):
    queryset = Snmp_Info.objects.all()
    serializer_class = SnmpSerializers

class Snmp_ViewInfo(generics.RetrieveUpdateDestroyAPIView):
    queryset = Snmp_Info.objects.all()
    serializer_class = SnmpSerializers
    permission_classes = (IsSuperAdminUser,)

class Disk_List(generics.ListCreateAPIView):
    queryset = Disk_Info.objects.all()
    serializer_class = DiskSerializers

class Disk_ViewInfo(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'osd'
    queryset = Disk_Info.objects.all()
    serializer_class = DiskSerializers

class Disk_Roam(generics.RetrieveUpdateDestroyAPIView):

    def post(self, request):
        if request.method == 'POST':
            osd = get_request_data(request)
            osdname = osd["name"].encode('utf-8')
            hostname = osd["hostname"].encode('utf-8')
            exec_diskroam.execa(osdname, hostname)
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=404)
            pass

    def get(self, request):
        return HttpResponse(status=404)
