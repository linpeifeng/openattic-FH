from rest_framework import serializers
from alerts.models import *

class AlertSerializers(serializers.ModelSerializer):
    class Meta:
        model = Alert_Info
        fields = ('time', 'level', 'location', 'details', 'ceph_mib')

class SnmpSerializers(serializers.ModelSerializer):
    class Meta:
        model = Snmp_Info
        fields = ('id', 'enabled', 'snmp_version', 'snmp_serverip',
                    'snmp_serverport', 'community_str', 'authmeth', 'authuser',
                    'authpasswd', 'engineid', 'authprotocol', 'privprotocol',
                    'privpasswd')

class DiskSerializers(serializers.ModelSerializer):
    class Meta:
        model = Disk_Info
        fields = ('wwn', 'hostname', 'osd', 'disk', 'solt', 'otherinfo')

