#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import salt.client
import requests
import configobj
import sys
import socket
import os, time, thread
from funclass import Slotletter
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
                'pool_used': '85',
                'alert_interval': '10'}

setvar = getSetting()
prometheus_ip = str(setvar['prometheus_ip'])
temperature_var = int(setvar['temperature_var'])
pool_used = int(setvar['pool_used'])
pool_readonly = 100
alert_interval = int(setvar['alert_interval'])

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

def salt_cmd(tgt, fun, arg=(), timeout=None, expr_form='list', ret='', jid='', **kwargs):
    try:
        local = salt.client.LocalClient()
        pub_data = local.run_job(tgt, fun, arg, expr_form, ret, timeout, jid, listen=True, **kwargs)
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

def insrt_alerts(time = None, insert_level = None, location = None, details = None, ceph_mib = None):
    try:
        if "Temperature" in details:
            strinfo = details.split("high")[0]
        else:
            strinfo = details
        if Alert_Info.objects.filter(details__contains=strinfo).filter(location=location).count() > 0:
            pass
        else:
            Alert_Info.objects.create(time=time, level=insert_level, location=location, details=details, ceph_mib=ceph_mib)
        CacheAlertInfo.objects.create(time=time, level=insert_level, location=location, details=details, ceph_mib=ceph_mib)
    except:
        return 'insert_error'

def checkalertinfo():
    try:
        allalert = Alert_Info.objects.values("details")
        for al in allalert:
            if "Temperature" in al["details"]:
                strinfo = al["details"].split("high")[0]
            else:
                strinfo = al["details"]
            if CacheAlertInfo.objects.filter(details__contains=strinfo).count() > 0:
                pass
            else:
                Alert_Info.objects.filter(details__contains=strinfo).delete()
    except:
        pass

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
                    detail = pool_name + ' Exceeded the threshold: ' + (
                                "%.2f%%" % pool_used)
                    insrt_alerts(time=now_time, insert_level=level,
                                 location=pool_name,
                                 details=detail, ceph_mib=miba)
                else:
                    pass

                if pool_usage == pool_readonly:
                    level = alert_level['0']
                    miba = ceph_mibs['PoolStatusError']
                    detail = pool_name + ':Read-only risk,pool status is abnormal'
                    insrt_alerts(time=now_time, insert_level=level,
                                 location=pool_name,
                                 details=detail, ceph_mib=miba)
                else:
                    pass
        conn.disconnect()

def poolus():
    conn = ceph_conn()
    try:
        if conn != 'conn_error':
            pool_list = conn.mon_command(cmd="health", argdict={"detail":"detail"})["detail"]
            if len(pool_list) > 0:
                for pool in pool_list:
                    if 'full' in pool:
                        pool_name = pool.split()[1].replace("'","")
                        level = alert_level['1']
                        mib = ceph_mibs['PoolCapacity']
                        insrt_alerts(time=now_time, insert_level=level, location=pool_name, details=pool, ceph_mib=mib)
            conn.disconnect()
    except:
        pass

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
            if '-' in osd['host']:
                host_in = osd['host'].split('-')[0]
            else:
                host_in = osd['host']
            host_list.append(host_in)
            hoststatus_list.append({host_in:osd['status']})
      for host in list(set(host_list)):
          host_ip = getdns(host)
          if pingip(host_ip) == 'error':
              node_level = alert_level['1']
              detail = 'IP: '+host_ip+' '+ host + ' Storage node down'
              miba = ceph_mibs['NodeStatusError']
              insrt_alerts(time=now_time, insert_level=node_level,
                           location=host, details=detail, ceph_mib=miba)
          else:
              pass
      conn.disconnect()

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

def gettemper(disk, host):
    storcli = "smartctl -s on -a -T permissive %s|grep 'Temperature_Celsius'|awk '{print $(NF-5)}'" % (disk)
    try:
      runsalt = salt_cmd(host,'cmd.run',[storcli])
      if runsalt != 'salt_error' and runsalt:
          retcode = runsalt[host]['retcode']
          if retcode == 0:
            return runsalt[host]['ret']
          else:
              return 'run command error: smartctl'
      else:
          return 'salt master error: smartctl'
    except:
      return 'salt master error: smartctl'

def gettemper_scsi():
    diskinfo = {
        'healthy': '/api/v1/query?query=smartmon_device_smart_healthy{disk!~"/dev/bus/0"}',
    }
    try:
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
                        hostvar = getdns(host, fullname=1)
                        ip = getdns(host)
                        if x['metric']['type'] == 'scsi' :
                            detail = ip + ' ' + host + ' ' + diskname + ' Temperature is too high '
                            tempervar = gettemper(diskname, hostvar)
                            if "error" not in tempervar and tempervar != "" and int(tempervar) >= temperature_var:
                                level = alert_level['3']
                        if level is not None:
                            sdxdisk = str(diskname).split("/")[-1]
                            slotinfo = Disk_Info.objects.filter(hostname=hostvar, disk=sdxdisk).values("solt").first()
                            print slotinfo
                            if slotinfo:
                                details = str(detail) +tempervar+'::'+ slotinfo["solt"]
                                insrt_alerts(time=now_time, insert_level=level, location=host, details=details, ceph_mib=mib)
                        else:
                            pass
                else:
                    stra = 'select promethus null'
                    insrt_alerts(time=now_time, insert_level=alert_level['3'], location=stra, details=stra, ceph_mib=ceph_mibs['NodeDisk'])
            else:
                stra = 'conn promethus api error'
                insrt_alerts(time=now_time, insert_level=alert_level['3'], location=stra, details=stra, ceph_mib=ceph_mibs['NodeDisk'])
    except:
        pass

def gettemper_nvme():
    disk = Disk_Info.objects.filter(disk__contains="nvme")
    try:
        for x in disk:
            detail = None
            level = None
            mib = ceph_mibs['NodeDisk']
            nvmetemp = "nvme smart-log %s|grep ^temperature|awk '{print $(NF-1)}'" % (x.disk)
            runsalta = salt_cmd(x.hostname, 'cmd.run', [nvmetemp])
            if runsalta != 'salt_error' and runsalta:
                retcode = runsalta[x.hostname]['retcode']
                restr = runsalta[x.hostname]['ret']
                if retcode == 0 and restr and "No such" not in restr:
                    if int(restr) >= temperature_var:
                        level = alert_level['3']
                        detail =  getdns(x.hostname) + ' ' + x.hostname + ' ' + x.disk + ' Temperature is too high %s ' % (restr)
                elif retcode == 0 and "No such" in restr:
                    level = alert_level['3']
                    detail = getdns(x.hostname) + ' ' + x.hostname + ' ' + x.disk + ' disk offline '
                if detail is not None and level is not None:
                    details = detail + '::' + x.solt
                    insrt_alerts(time=now_time, insert_level=level, location=x.hostname, details=details, ceph_mib=mib)
    except:
        pass

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
                    '''
                    elif disk == 'healthy' and 'dev' in diskname:
                        if x['value'][1] != '1' and x['metric']['type'] == 'sat' :
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Sub-health'
                        if x['value'][1] != '0' and x['metric']['type'] == 'scsi' :
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Sub-health'
                    elif disk == 'temperature' and 'dev' in diskname:
                        if int(x['value'][1]) >= temperature_var:
                            level = alert_level['3']
                            detail = ip + ' ' + host + ' ' + diskname + ' Temperature is too high %s ' % (x['value'][1])
                    '''
                    if detail is not None and level is not None:
                        sdxdisk = str(diskname).split("/")[-1]
                        slotinfo = Disk_Info.objects.filter(hostname=getdns(host, fullname=1), disk=sdxdisk).values("solt").first()
                        if slotinfo:
                            details = str(detail) +'::'+ slotinfo["solt"]
                            insrt_alerts(time=now_time, insert_level=level, location=host, details=details, ceph_mib=mib)
                    else:
                        pass
            else:
                stra = 'select promethus null'
                insrt_alerts(time=now_time, insert_level=alert_level['3'], location=stra, details=stra, ceph_mib=ceph_mibs['NodeDisk'])
        else:
            stra = 'conn promethus api error'
            insrt_alerts(time=now_time, insert_level=alert_level['3'], location=stra, details=stra, ceph_mib=ceph_mibs['NodeDisk'])

def diskoffline():
  disk = Disk_Info.objects.exclude(disk__contains="nvme")
  mib = ceph_mibs['NodeDisk']
  for x in disk:
    detail = None
    level = None
    try:
      inip = getdns(x.hostname)
      if 'error' not in x.solt and pingip(inip) != 'error':
          disk_wwn = Slotletter().getwnsn_sas3ircu(x.solt.split(' ')[2], x.hostname)

      if 'error' not in disk_wwn and disk_wwn != "null":
        pass
      elif disk_wwn == "null" and pingip(inip) != 'error':
        level = alert_level['1']
        detail =inip + ' ' + x.hostname + ' ' + x.disk + ' disk offline '

      if detail is not None and level is not None:
        details = detail +'::'+ x.solt
        insrt_alerts(time=now_time, insert_level=level, location=x.hostname, details=details, ceph_mib=mib)
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
                if '-' in osd['host']:
                    host_in = osd['host'].split('-')[0]
                else:
                    host_in = osd['host']
                nodehost = host_in
                hoststatus_list.append({host_in: osd['status']})
                osdid = osd['id']
            if osd['status'] == 'down' and {nodehost: 'up'} in hoststatus_list:
                comm_df = "lsblk -s|grep ceph-%s -A3|grep disk|grep sd|awk '{print $1}'" % (osdid)
                hosttema = getdns(nodehost, fullname=1)
                runsalta = salt_cmd(hosttema, 'cmd.run', [comm_df])
                if runsalta != 'salt_error' and runsalta:
                    retcode = runsalta[hosttema]['retcode']
                    if "-" in runsalta[hosttema]['ret']:
                        redisk = runsalta[hosttema]['ret'].split("-")[1]
                    else:
                        redisk = None
                    if retcode == 0 and redisk:
                        smarta = "smartctl -s on -a -T permissive /dev/" + redisk + "|grep 'Serial [Nn]umber'|awk '{print $NF}'"
                        runsaltb = salt_cmd(hosttema, 'cmd.run', [smarta])
                        if runsaltb != 'salt_error' and runsaltb:
                            retcode = runsaltb[hosttema]['retcode']
                            if retcode == 0:
                                if runsaltb[hosttema]['ret'] == '':
                                    detail = 'osd-%s service down :: disk %s offline' % (osdid, redisk)
                                else:
                                    detail = 'osd-%s service down :: disk %s ' % (osdid, redisk)
                                slots = Disk_Info.objects.filter(hostname=hosttema).filter(osd='osd-%s' % (osdid)).filter(disk=redisk)
                                if slots.count() > 0:
                                    stra = detail+'::'+list(slots.values('solt'))[0]['solt']
                                else:
                                    stra = detail+' :: get slot error'
                            else:
                                stra = 'osd-%s service down :: exec smartctl error' % (osdid)
                        else:
                            stra = 'salt master error'
                    else:
                        stra = 'osd-%s service down' % (osdid)
                else:
                    stra = 'salt master error'
                insrt_alerts(time=now_time, insert_level=level, location=hosttema, details=stra, ceph_mib=mib)
            else:
                continue
        conn.disconnect()
    else:
        stra = 'conn ceph error'
        insrt_alerts(time=now_time, insert_level=alert_level['1'], location=stra, details=stra, ceph_mib=ceph_mibs['NodeStatusError'])

while 1:
    now_time = datetime.now()+timedelta(hours=6)
    with transaction.atomic():
        #Alert_Info.objects.all().delete()
        CacheAlertInfo.objects.all().delete()
        poolusage()
        #poolus()
        pooldegrade()
        poolrecovery()
        thread.start_new_thread(nodestatus_osd, ())
        nodedisk()
        gettemper_scsi()
        gettemper_nvme()
        thread.start_new_thread(diskoffline, ())
        #diskstatus()
        sendsnmp()
        checkalertinfo()
    time.sleep(alert_interval)