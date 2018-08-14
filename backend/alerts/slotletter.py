#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import salt.client
import sys, socket, os
import time
sys.path.append("/usr/share/openattic")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from alerts.models import *
from librados import *
from django.db import transaction

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

def insrt_disk(wwna=None, hosta=None, osda=None, diska=None, solta=None):
    try:
        Disk_Info.objects.create(wwn= wwna, hostname=hosta,
                                 osd=osda, disk=diska, solt=solta)
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
              srecode = runsalt[host]['retcode']
              if srecode == 0:
                reinfos = restorcli[host]['ret'].split('\n')
                raid = reinfos[0].split('/')[1]
                for stinfo in reinfos:
                  if 'EID:Slt' in stinfo:
                    esid = reinfos[reinfos.index(stinfo)+2].split(' ')[0].split(':')
                    stwn = '/%s/e%s/s%s' % (raid, esid[0], esid[1])
                    wwn = getslotwwn(stwn,host).split(':')
                    restra = 'Serial Number: %s :: RaidID: %s :: Enclosure Device ID: %s :: Slot Number: %s' % (wwn[1],raid,esid[0],esid[1])
                    return restra+'**'+wwn[0]
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
      return restra+'**'+wwn
    except:
      return 'get slot error'

def getslot(disk,host):
  raid_info = check_raid(disk,host)
  if raid_info == '':
    return getslot_raid(disk,host)
  else:
    return getslotnoraid(disk,host)

def getslot_host():
    conn = ceph_conn()
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
            comm_df = "df -h|grep ceph-%s$|awk -F ' ' '{print $1}'|awk -F " \
                          "'[0-9]*' '{print $1}'" % (osdid)
            hostname = getdns(nodehost, fullname=1)
            runsalta = salt_cmd(hostname, 'cmd.run', [comm_df])
            if runsalta != 'salt_error' and runsalta:
                retcode = runsalta[hostname]['retcode']
                if retcode == 0 and runsalta[hostname]['ret']:
                    stra = getslot(runsalta[hostname]['ret'], hostname)
                    if '**' in stra:
                        wwnnum = stra.split('**')[1]
                        slotinfo = stra.split('**')[0]
                    else:
                        wwnnum = None
                        slotinfo = stra
                    diskb = runsalta[hostname]['ret']
                else:
                    wwnnum = None
                    diskb = 'osd.%s service :: get /dev/sd** error' % (osdid)
                    slotinfo = getslot(runsalta[hostname]['ret'], hostname)
                if 'error' not in slotinfo and 'error' not in diskb and wwnnum is not None:
                    with transaction.atomic():
                        try:
                            Disk_Info.objects.get(wwn=wwnnum).delete()
                            Disk_Info.objects.filter(hostname=hostname, osd='osd.%s' % (osdid), diska=diskb).delete()
                        except:
                            pass
                        insrt_disk(wwna=wwnnum, hosta=hostname,
                                   osda='osd.%s' % (osdid), diska=diskb,
                                   solta=slotinfo)
                elif wwnnum is not None:
                    with transaction.atomic():
                        try:
                            Disk_Info.objects.get(wwn=wwnnum).delete()
                            Disk_Info.objects.filter(hostname=hostname, osd='osd.%s' % (osdid), diska=diskb).delete()
                        except:
                            pass
                        insrt_disk(wwna=wwnnum, hosta=hostname,
                                   osda='osd.%s' % (osdid), diska=diskb,
                                   solta=slotinfo)
            else:
                pass
        conn.disconnect()
    else:
        pass

while 1:
    getslot_host()
    time.sleep(1800)