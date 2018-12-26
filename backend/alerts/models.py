from django.db import models


# Create your models here.

class Alert_Info(models.Model):
    LEVEL_CHOICE = (
        (u'critical', 'critical'),
        (u'major', 'major'),
        (u'info', 'info'),
        (u'minor', 'minor'),
    )
    time = models.DateTimeField(max_length=20, default='null')
    level = models.CharField(max_length=20, default='critical',
                             choices=LEVEL_CHOICE)
    location = models.CharField(max_length=100, default='null')
    details = models.CharField(max_length=200, default='null')
    ceph_mib = models.CharField(max_length=200, default='null')

    class Meta:
        ordering = ('time', 'level', 'location', 'details', 'ceph_mib')

class CacheAlertInfo(models.Model):
    LEVEL_CHOICE = (
        (u'critical', 'critical'),
        (u'major', 'major'),
        (u'info', 'info'),
        (u'minor', 'minor'),
    )
    time = models.DateTimeField(max_length=20, default='null')
    level = models.CharField(max_length=20, default='critical',
                             choices=LEVEL_CHOICE)
    location = models.CharField(max_length=100, default='null')
    details = models.CharField(max_length=200, default='null')
    ceph_mib = models.CharField(max_length=200, default='null')

    class Meta:
        ordering = ('time', 'level', 'location', 'details', 'ceph_mib')


class Snmp_Info(models.Model):
    SNMP_VERSION = ((u'0', 'v2c'), (u'1', 'v3'))

    AUTH_CHO = (
        (u'noAuthNoPriv', 'noAuthNoPriv'),
        (u'authNoPriv', 'authNoPriv'),
        (u'authPriv', 'authPriv'))

    AUTHPROTOCOL_CHO = ((u'MD5', 'MD5'), (u'SHA', 'SHA'))
    PRIVROTOCOL_CH = ((u'DES', 'DES'), (u'AES', 'AES'))

    id = models.AutoField(primary_key=True)
    enabled = models.BooleanField(default=False, null=False)
    snmp_version = models.CharField(max_length=20, default=0,
                                    choices=SNMP_VERSION, null=False)
    snmp_serverip = models.CharField(max_length=30, default='null', null=False)
    snmp_serverport = models.IntegerField(default=162, null=False)
    community_str = models.CharField(max_length=20, default='null', null=True,
                                     blank=True)
    authmeth = models.CharField(max_length=20, default='noAuthNoPriv',
                                null=True,
                                blank=True, choices=AUTH_CHO)
    authuser = models.CharField(max_length=30, default='null', null=True,
                                blank=True)
    authpasswd = models.CharField(max_length=30, default='null', null=True,
                                  blank=True)
    engineid = models.CharField(max_length=30, default='null', null=True,
                                blank=True)
    authprotocol = models.CharField(max_length=30, default='MD5', null=True,
                                    blank=True, choices=AUTHPROTOCOL_CHO)
    privprotocol = models.CharField(max_length=30, default='DES', null=True,
                                    blank=True, choices=PRIVROTOCOL_CH)
    privpasswd = models.CharField(max_length=30, default='', null=True,
                                  blank=True)

    class Meta:
        ordering = ('id', 'enabled', 'snmp_version', 'snmp_serverip',
                    'snmp_serverport', 'community_str', 'authmeth', 'authuser',
                    'authpasswd', 'engineid', 'authprotocol', 'privprotocol',
                    'privpasswd')


class Disk_Info(models.Model):
    wwn = models.CharField(primary_key=True, max_length=50, default='null',
                           null=False)
    hostname = models.CharField(max_length=50, default='null', null=False)
    osd = models.CharField(max_length=50, default='null', null=True)
    disk = models.CharField(max_length=50, default='null', null=True)
    solt = models.CharField(max_length=300, default='null', null=False)
    otherinfo = models.CharField(max_length=300, default='null', null=True,
                                 blank=True)

    class Meta:
        ordering = ('wwn', 'hostname', 'osd', 'disk', 'solt', 'otherinfo')
