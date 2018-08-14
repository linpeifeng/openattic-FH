#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import salt.client
import six
import requests
import configobj
import sys
import socket
import os, time
from datetime import datetime, timedelta
sys.path.append("/usr/share/openattic/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from alerts.models import *
from librados import *
from django.db import transaction

alert_level = {'0':'critical', '1':'major', '2':'info', '3':'minor'}
ceph_mibs = {
    'PoolCapacity': '1.3.6.1.4.1.50495.1.8',
    'PoolStatusError': '1.3.6.1.4.1.50495.1.9',
    'PoolDegradation': '1.3.6.1.4.1.50495.1.10',
    'NodeStatusError': '1.3.6.1.4.1.50495.1.11',
    'NodeDisk': '1.3.6.1.4.1.50495.1.12'
}

def getSetting():
    if os.path.exists('/etc/openattic/alertsvar.conf'):
        local_settings_file = os.path.join(sys.path[0], '/etc/openattic/alertsvar.conf')
        snmpsetting = {}
        if os.access(local_settings_file, os.R_OK):
            for key, val in configobj.ConfigObj(local_settings_file).items():
                snmpsetting[key] = val
        return snmpsetting
    else:
        return {'prometheus_ip': '127.0.0.1:9090',
                'temperature_var': '60',
                'pool_readonly': '96',
                'pool_used': '85'}

prometheus_ip = str(getSetting()['prometheus_ip'])
temperature_var = int(getSetting()['temperature_var'])
pool_used = int(getSetting()['pool_used'])
pool_readonly = int(getSetting()['pool_readonly'])

#:*****************************

def prometheus_api(promsql=None, api=None):
    try:
        if promsql is None:
            response = requests.get('http://'+prometheus_ip+api).json()
        else:
            response = requests.get('http://' + prometheus_ip + api,
                                    params=promsql).json()
    except:
        response = 'conn_error'
    return response


def pingip(ip):
    try:
        exec_pro = subprocess.Popen('ping -c 1 %s'%ip, shell=True, universal_newlines=True,
                         stdout=subprocess.PIPE).communicate()[0]
        #ret_ip = exec_pro.replace('(','').replace(')','').split(' ')[2]
        ret_ip = '100% packet loss' in exec_pro
        if ret_ip:
            ret = 'error'
        else:
            ret = 'ok'
    except:
        ret = 'error'
    return ret


def getdns(hostname,fullname=None):
    try:
        if fullname is None:
            hostip = socket.gethostbyname(hostname)
        else:
            hostip = socket.getfqdn(name=hostname)
        if hostip:
          ret = hostip
        else:
            ret = 'dns_error'
    except:
        ret = 'dns_error'
    return ret

def exec_comm(comm):
    try:
        exec_pro = subprocess.Popen(comm, shell=True, universal_newlines=True,
                         stdout=subprocess.PIPE)
        exec_pro.wait()
        if exec_pro.returncode == 0:
            ret = 0
        else:
            ret = 'error'
    except:
        ret = 'error'
    return ret


def salt_cmd(tgt,
             fun,
             arg=(),
             timeout=None,
             expr_form='list',
             ret='',
             jid='',
             **kwargs):
    try:
        local = salt.client.LocalClient()
        pub_data = local.run_job(tgt, fun, arg, expr_form, ret, timeout, jid,
                                 listen=True, **kwargs)

        if not pub_data:
            return pub_data
        ret = {}
        fn_rets = local.get_cli_event_returns(
            pub_data['jid'],
            pub_data['minions'],
            timeout,
            tgt,
            expr_form,
            **kwargs)

        for fn_ret in fn_rets:
            for mid, data in six.iteritems(fn_ret):
                ret[mid] = data

        for failed in list(set(pub_data['minions']) ^ set(ret.keys())):
            key = {}
            key["retcode"] = 1
            key["ret"] = "Salt minion is Down"
            ret[failed] = key

    except:
        ret = 'salt_error'
    return ret


def insrt_alerts(time = None, insert_level = None, location = None,
                     details = None, ceph_mib = None):
    try:
        Alert_Info.objects.create(time=time, level=insert_level,
                                  location=location, details=details,
                                  ceph_mib=ceph_mib)
    except:
        return 'insert_error'


def ceph_conn():
    try:
        client = Client()
        if client.connected():
            return client
        else:
            return 'conn_error'
    except:
        return 'conn_error'


def pooldegrade():
    conn = ceph_conn()
    if conn != 'conn_error':
        for pool in conn.list_pools():
            poo_name = pool
            deg_num =conn.get_pool(pool).get_stats()['num_objects_degraded']
            if deg_num != 0:
                deg_level = alert_level['1']
                detail = poo_name + ' Pool Degraded'
                miba = ceph_mibs['PoolDegradation']
                insrt_alerts(time=now_time, insert_level=deg_level,
                             location=poo_name,
                             details=detail, ceph_mib=miba)
            else:
               pass
        conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'], location=stra,
                     details=stra, ceph_mib=ceph_mibs['NodeStatusError'])


def poolusage():
    conn = ceph_conn()
    if conn != 'conn_error':
        pool_list = conn.mon_command(cmd="df")['pools']
        if len(pool_list) > 0:
            for pool in pool_list:
                pool_name = pool['name']
                pool_usage = pool['stats']['percent_used']
                if pool_usage > pool_used:
                    level = alert_level['1']
                    miba = ceph_mibs['PoolCapacity']
                    detail = pool_name + ' Capacity is used: ' + (
                                "%.2f%%" % pool_usage)
                    insrt_alerts(time=now_time, insert_level=level,
                                 location=pool_name,
                                 details=detail, ceph_mib=miba)
                else:
                    pass

                if pool_usage > pool_readonly:
                    level = alert_level['0']
                    miba = ceph_mibs['PoolStatusError']
                    detail = pool_name + ':Read-only risk,Serious shortage of space'
                    insrt_alerts(time=now_time, insert_level=level,
                                 location=pool_name,
                                 details=detail, ceph_mib=miba)

                else:
                    pass
        conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'],
                     location=stra,
                     details=stra, ceph_mib=ceph_mibs['NodeStatusError'])


def poolrecovery():
    conn = ceph_conn()
    if conn != 'conn_error':
        pool_list = conn.mon_command(cmd='osd pool stats')
        if len(pool_list) > 0:
            for pool in pool_list:
                pool_name = pool['pool_name']
                pool_recover = pool['recovery_rate']
                if pool_recover :
                    level = alert_level['0']
                    detail = pool_name + ' Pool Status Recoverying'
                    miba = ceph_mibs['PoolStatusError']
                    insrt_alerts(time=now_time, insert_level=level,
                                 location=pool_name,
                                 details=detail, ceph_mib=miba)
                else:
                    pass
        conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'],
                     location=stra,
                     details=stra, ceph_mib=ceph_mibs['NodeStatusError'])


def nodestatus_osd():
    conn = ceph_conn()
    if conn != 'conn_error':
      host_list = []
      hoststatus_list = []
      for osd in conn.osd_list():
        try:
          osd['host']
        except:
          pass
        else:
          host_list.append(osd['host'])
          hoststatus_list.append({osd['host']:osd['status']})
      for host in list(set(host_list)):
          host_ip = getdns(host)
          if {host:'up'} not in hoststatus_list and pingip(host_ip) == 'error':
              node_level = alert_level['1']
              detail = 'IP: '+host_ip+' '+ host + ' Storage node down'
              miba = ceph_mibs['NodeStatusError']
              insrt_alerts(time=now_time, insert_level=node_level,
                           location=host,
                           details=detail, ceph_mib=miba)
          else:
              pass
      conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'], location=stra,
                     details=stra, ceph_mib=ceph_mibs['NodeStatusError'])


def snmptrap(mibs, detail):
    try:
        try:
            snmpserver = 0
            Snmp_Info.objects.filter(enabled=False).delete()
            vara = Snmp_Info.objects.all()
            for x in vara:
                snmpserver = x
        except:
            snmpserver = 0
        if snmpserver != 0 and snmpserver.enabled == True :
            version = snmpserver.snmp_version
            ipport = snmpserver.snmp_serverip+':'+str(snmpserver.snmp_serverport)
            community = snmpserver.community_str
            auths = snmpserver.authmeth
            authpro = snmpserver.authprotocol
            authuser = snmpserver.authuser
            authpasswd = snmpserver.authpasswd
            privs = snmpserver.privprotocol
            privpasswd = snmpserver.privpasswd
            if version == '0':
                snmpv2 = 'snmptrap -v 2c -c %s %s "" 1.3.6.1.4.1.50495 %s s "%s"' % (community, ipport, mibs, detail)
                exec_comm(snmpv2)
            elif version == '1':
                snmpv3 = ''
                if auths == 'noAuthNoPriv':
                    snmpv3 = 'snmptrap -v 3 -u %s -l noAuthNoPriv %s ""' \
                              ' 1.3.6.1.4.1.50495 %s s "%s"' % (authuser, ipport, mibs, detail)
                elif auths == 'authNoPriv':
                    snmpv3 = 'snmptrap -v 3 -u %s -a %s -A %s -l ' \
                             'authNoPriv %s "" 1.3.6.1.4.1.50495 %s s "%s"' % \
                             (authuser, authpro, authpasswd, ipport,
                              mibs, detail)
                elif auths == 'authPriv':
                    snmpv3 = 'snmptrap -v 3 -u %s -a %s -A %s -l authPriv ' \
                             '-x %s -X %s %s "" 1.3.6.1.4.1.50495 %s s "%s"' % \
                             (authuser, authpro, authpasswd, privs,
                              privpasswd, ipport, mibs, detail)
                exec_comm(snmpv3)
    except:
        pass


def sendsnmp():
    alerts = Alert_Info.objects.exclude(level__contains=alert_level['2']).values \
        ('time', 'level', 'location', 'details', 'ceph_mib')
    for alertx in alerts:
        mib = alertx['ceph_mib']
        detail = 'level: ' + alertx['level'] + ', ' + alertx['details']
        snmptrap(mib, detail)


def getslotwwn(disk,host):
    storcli_wwn = "storcli "+disk+" show all |grep WWN && "+"storcli "+disk+" show all |grep 'SN ='"
    wwn = ''
    try:
      runsalt = salt_cmd(host,'cmd.run',[storcli_wwn])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            wwn = runsalt[host]['ret'].replace(' ','').split('\n')[0].split('=')[1]
            sn = runsalt[host]['ret'].replace(' ','').split('\n')[1].split('=')[1]
            return wwn+':'+sn
          else:
              return 'run command error: storcli wwn'
      else:
          return 'salt master error: storcli wwn'
    except:
      return 'salt master error: storcli wwn'

def getslotesid(wwn,host):
    storcli_wwn = "storcli /call/eall/sall show all | grep "+wwn+" -B37 -A52"
    try:
      runsalt = salt_cmd(host,'cmd.run',[storcli_wwn])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            return runsalt[host]['ret'].replace(' ','').split('\n')[0].replace('Drive','').replace(':','')
          else:
              return 'run command error: storcli eid sid'
      else:
          return 'salt master error: storcli eid sid'
    except:
      return 'salt master error: storcli eid sid'

def getslot_raid(disk,host):
    smartctl_wwn = "smartctl -s on -a -T permissive " + disk + "|grep 'Logical Unit id'|awk -F '0x' '{print $2}'"
    wwna = ''
    try:
      runsalt = salt_cmd(host,'cmd.run',[smartctl_wwn])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            wwna = runsalt[host]['ret'].replace(' ','')
            storcli_wwn = "storcli /call/vall show all|grep -i "+wwna+" -B53"
            restorcli = salt_cmd(host,'cmd.run',[storcli_wwn])
            if restorcli != 'salt_error' and restorcli:
              srecode = restorcli[host]['retcode']
              if srecode == 0:
                reinfos = restorcli[host]['ret'].split('\n')
                raid = reinfos[0].split('/')[1]
                for stinfo in reinfos:
                  if 'EID:Slt' in stinfo:
                    esid = reinfos[reinfos.index(stinfo)+2].split(' ')[0].split(':')
                    stwn = '/%s/e%s/s%s' % (raid, esid[0], esid[1])
                    wwn = getslotwwn(stwn,host).split(':')
                    restra = 'Serial Number: %s :: RaidID: %s :: Enclosure Device ID: %s :: Slot Number: %s' % (wwn[1],raid,esid[0],esid[1])
                    return restra
              else:
                return 'run command error: storcli'
            else:
              return 'salt master error: exec storcli'
          else:
              return 'run command error: smartctl'
      else:
          return 'salt master error'
    except:
      return 'get slot error'


def check_raid(disk,host):
    smartctl_wwn = "smartctl -s on -a -T permissive " + disk + "|grep WWN|awk -F ':' '{print $2}'"
    runsalt = salt_cmd(host,'cmd.run',[smartctl_wwn])
    if runsalt != 'salt_error' and runsalt:
        retcode = runsalt[host]['retcode']
        if retcode == 0:
          return runsalt[host]['ret'].replace(' ','')
        else:
            return 'run command error: %s' % (smartctl_wwn)
    else:
        return 'salt master error'


def getslotnoraid(disk,host):
    smartctl_wwn = "smartctl -s on -a -T permissive " + disk + "|grep WWN|awk -F ':' '{print $2}'"
    sernums = "smartctl -s on -a -T permissive " + disk + "|grep 'Serial Number'|awk -F ' ' '{print $3}'"
    wwn = sernum = ''
    try:
      for x in (smartctl_wwn, sernums):
          runsalt = salt_cmd(host,'cmd.run',[x])
          if runsalt != 'salt_error' and runsalt:
              retcode = runsalt[host]['retcode']
              if retcode == 0:
                  if x == smartctl_wwn:
                      wwn = runsalt[host]['ret'].replace(' ','')
                  else:
                      sernum = runsalt[host]['ret'].replace(' ','')
              else:
                  return 'run command error: %s' % (x)
          else:
              return 'salt master error get slot'
      if 'error' not in getslotesid(wwn, host):
        esid = getslotesid(wwn, host).split('/')
        restra = 'Serial Number: %s :: RaidID: %s :: Enclosure Device ID: %s :: Slot Number: %s' % (sernum,esid[1],esid[2],esid[3])
      else:
        esid = 'get eID slotID error'
        restra = 'Serial Number: %s :: RaidID: %s :: Enclosure Device ID: %s :: Slot Number: %s' % (sernum,'Nofound','Nofound','Nofound')
      return restra
    except:
      return 'get slot error'

def getslot(disk,host):
  raid_info = check_raid(disk,host)
  if raid_info == '':
    return getslot_raid(disk,host)
  else:
    return getslotnoraid(disk,host)


def nodedisk():
    diskinfo = {
        'offlinetest': '/api/v1/query?query=smartmon_offline_uncorrectable_raw_value{disk!~"/dev/bus/0"}',
        'healthy': '/api/v1/query?query=smartmon_device_smart_healthy{disk!~"/dev/bus/0"}',
        'temperature': '/api/v1/query?query=smartmon_temperature_celsius_raw_value{disk!~"/dev/bus/0"}',
    }

    for disk in diskinfo.keys():
        diskdata = prometheus_api(api=diskinfo[disk])
        if diskdata != 'conn_error':
            if diskdata['status'] == 'success':
                for x in diskdata['data']['result']:
                    detail = None
                    level = None
                    mib = ceph_mibs['NodeDisk']
                    diskname = x['metric']['disk']
                    host = x['metric']['instance'].split(':')[0]
                    ip = getdns(host)
                    if disk == 'offlinetest' and 'dev' in diskname:
                        if x['value'][1] != '0':
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + 'Offline test error'
                    elif disk == 'healthy' and 'dev' in diskname:
                        if x['value'][1] != '1' and x['metric']['type'] == 'sat' :
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Sub-health'
                        if x['value'][1] != '0' and x['metric']['type'] == 'scsi' :
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Sub-health'
                    '''
                    elif disk == 'temperature' and 'dev' in diskname:
                        if int(x['value'][1]) >= temperature_var:
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Temperature is too high %s ' % (x['value'][1])
                    '''
                    if detail is not None and level is not None:
                        details = detail +'::'+ getslot(diskname,getdns(host,fullname=1))
                        insrt_alerts(time=now_time, insert_level=level,
                                     location=host,
                                     details=details, ceph_mib=mib)
                    else:
                        pass
            else:
                stra = 'select promethus null'
                insrt_alerts(time=now_time, insert_level=alert_level['3'],
                             location=stra,
                             details=stra,
                             ceph_mib=ceph_mibs['NodeDisk'])
        else:
            stra = 'conn promethus api error'
            insrt_alerts(time=now_time, insert_level=alert_level['3'],
                         location=stra,
                         details=stra,
                         ceph_mib=ceph_mibs['NodeDisk'])

def gettemper(rid,eid,sid,host):
    storcli = "storcli /%s/e%s/s%s show all | grep Temperature" % (rid, eid, sid)
    try:
      runsalt = salt_cmd(host,'cmd.run',[storcli])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            return runsalt[host]['ret'].split(' ')[4].replace('C', '')
          else:
              return 'run command error: storcli'
      else:
          return 'salt master error: sstorcli'
    except:
      return 'salt master error: storcli'

def getdiskwwn(rid,eid,sid,host):
    storcli_wwn = "storcli /%s/e%s/s%s show all | grep WWN" % (rid, eid, sid)
    try:
      runsalt = salt_cmd(host,'cmd.run',[storcli_wwn])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            return runsalt[host]['ret']
          else:
              return 'run command error: storcli'
      else:
          return 'salt master error: storcli'
    except:
      return 'salt master error: storcli'

def disktemper():
  disk = Disk_Info.objects.all()
  mib = ceph_mibs['NodeDisk']
  for x in disk:
    detail = None
    level = None
    try:
      if pingip(getdns(x.hostname)) == 'error':
        continue
      elif pingip(getdns(x.hostname)) == 'ok':
        if 'error' not in x.solt:
          temper = gettemper(x.solt.split(' ')[5],x.solt.split(' ')[10],x.solt.split(' ')[14],x.hostname)
        if 'error' not in temper and int(temper) >= temperature_var:
          level = alert_level['3']
          detail = getdns(x.hostname) + ' ' + x.hostname + ' ' + x.disk + ' Temperature is too high %s ' % (temper)
        if detail is not None and level is not None:
          details = detail +'::'+ x.solt
          insrt_alerts(time=now_time, insert_level=level, location=x.hostname, details=details, ceph_mib=mib)
        else:
          pass
    except:
      pass


def diskstatus():
    conn = ceph_conn()
    mib = ceph_mibs['NodeDisk']
    level = alert_level['3']
    if conn != 'conn_error':
        hoststatus_list = []
        for osd in conn.osd_list():
            try:
              osd['host']
            except:
              pass
            else:
              nodehost = osd['host']
              hoststatus_list.append({osd['host']: osd['status']})
              osdid = osd['id']
              hostname = getdns(nodehost, fullname=1)
            if osd['status'] == 'down' and {nodehost: 'up'} in hoststatus_list:
              slots = Disk_Info.objects.filter(hostname=hostname).filter(osd='osd.%s' % (osdid))
              if slots.count() > 0:
                  solt = list(slots.values('solt'))[0]['solt']
                  disk_wwn = getdiskwwn(solt.split(' ')[5],solt.split(' ')[10],solt.split(' ')[14],hostname)
                  sel_wwn = list(slots.values('wwn'))[0]['wwn']
                  disk = list(slots.values('disk'))[0]['disk']
                  detail = None
                  if 'error' not in disk_wwn and sel_wwn in disk_wwn:
                    pass
                  elif 'error' not in disk_wwn and sel_wwn not in disk_wwn and 'WWN' in disk_wwn:
                    pass
                  else:
                    level = alert_level['3']
                    detail = getdns(hostname) + ' ' + hostname + ' ' + disk + ' disk offline '
                  if detail is not None and level is not None:
                    details = detail +'::'+ solt
                    insrt_alerts(time=now_time, insert_level=level, location=hostname, details=details, ceph_mib=mib)
                  else:
                    pass
            else:
                continue
        conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'], location=stra,
                     details=stra, ceph_mib=ceph_mibs['NodeStatusError'])

while 1:
    now_time = datetime.now()+timedelta(hours=6)
    with transaction.atomic():
      Alert_Info.objects.all().delete()
      poolusage()
      pooldegrade()
      poolrecovery()
      nodestatus_osd()
      nodedisk()
      diskstatus()
      sendsnmp()
    disktemper()
    time.sleep(5)
