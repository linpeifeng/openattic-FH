# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from alerts.views import *


urlpatterns = patterns('',
    url(r'^api/ceph_alerts$', Alert_List.as_view()),
    url(r'^api/disk_info$', Disk_List.as_view()),
    url(r'^api/disk_roam$', Disk_Roam.as_view()),
    url(r'^api/disk_info/(?P<osd>[a-z\.0-9]*)$', Disk_ViewInfo.as_view()),
    url(r'^api/ceph_alerts/snmp$', Snmp_List.as_view()),
    url(r'^api/ceph_alerts/snmp/(?P<pk>\d{1,3})$', Snmp_ViewInfo.as_view())
)
