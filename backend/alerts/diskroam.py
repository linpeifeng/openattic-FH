#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys, os
sys.path.append("/usr/share/openattic")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import salt.client
import sys
import socket
import time
import getopt
from alerts.models import *
from librados import *


#:*****************************
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
    except Exception, e:
        ret = 'salt_error'
    return ret


def ceph_conn():
    try:
        client = Client()
        if client.connected():
            return client
        else:
            return 'conn_error'
    except:
        return 'conn_error'


def diskinfo_save(osda, disks, infos):
    print infos
    try:
        diskinfo = Disk_Info.objects.get(osd=osda)
    except:
        return 'insert_error'
    else:
        if disks is not None:
            diskinfo.disk = disks
            diskinfo.save()
        elif infos is not None:
            diskinfo.otherinfo = infos
            diskinfo.save()
        else:
            pass


def osdstate(osdname, host):
    try:
        id = int((osdname).split('.')[1])
    except:
        id = 'error'
    if id != 'error':
        restartosd = 'systemctl restart ceph-osd@%s.service' % (id)
        osdstatus = 'ceph osd tree|grep osd.%s' % (id)
        lista = [restartosd, osdstatus]
        for act in lista:
            runsalta = salt_cmd(host, 'cmd.run', [act])
            if runsalta != 'salt_error' and runsalta:
                resulta = runsalta[host]['ret']
                if act == osdstatus:
                    if 'up' in resulta:
                        return 'up'
                    else:
                        return 'down'
                time.sleep(15)
            else:
                stra = 'get osd status: salt master error'
                diskinfo_save(osdname, None, stra)
                sys.exit(0)
    else:
        stra = 'get osd status: get osd name error'
        pass

def activeosd(osdname, host, disk):
    try:
        id = int((osdname).split('.')[1])
    except:
        id = 'error'
    if id != 'error':
        osdservice = 'systemctl stop ceph-osd@%s.service' % (id)
        umountdir = 'umount /var/lib/ceph/osd/ceph-%s' % (id)
        activedisk = 'ceph-disk activate %s1' % (disk)
        osdstatus = 'ceph osd tree|grep osd.%s' % (id)
        lista = [osdservice, umountdir, activedisk, osdstatus]
        hosttema = getdns(host, fullname=1)
        flaga = osdstate(osdname, hosttema)
        if flaga == 'up':
            diskinfo_save(osdname, None, 'No need to perform disk roaming')
        elif flaga == 'down':
            for act in lista:
                if act == activedisk or act == umountdir:
                    time.sleep(10)
                elif act == osdstatus:
                    time.sleep(15)
                runsalta = salt_cmd(hosttema, 'cmd.run', [act])
                if runsalta != 'salt_error' and runsalta:
                    resulta = runsalta[hosttema]['ret']
                    if runsalta[hosttema]['retcode'] != 0:
                        stra = 'activeing osd exception pls check: '+activedisk
                        if 'not mounted' in stra:
                            continue
                        else:
                            diskinfo_save(osdname, None, stra)
                            break
                    else:
                        if act == osdstatus:
                            if 'up' in resulta:
                                stra = 'Disk roaming sucessed'
                                diskinfo_save(osdname, None, stra)
                            else:
                                pass
                else:
                    stra = 'activeing osd salt master error'
                    diskinfo_save(osdname, None, stra)
        else:
            pass
    else:
        stra = 'activeing osd get osd name error'
        pass


def diskstatus(osdname, host):
    hosttema = getdns(host, fullname=1)
    try:
        diskinfoc = Disk_Info.objects.get(osd=osdname)
    except:
        diskinfoc = 'null'
    if diskinfoc != 'null':
        wwna = diskinfoc.wwn
        alldisk = "for x in `smartctl --scan|awk -F ' ' '{print $1}'|awk -F " \
                  "'[0-9]*' '{print $1}'`; do echo '###########\n' $x && " \
                  "smartctl -s on -a -T permissive $x; done"
        runsalta = salt_cmd(hosttema, 'cmd.run', [alldisk])
        if runsalta != 'salt_error' and runsalta:
            resulta = runsalta[hosttema]['ret']
            for x in resulta.split('###########'):
                if 'WWN' in x:
                    resultb = x.split('\n')
                    diskx = resultb[1].replace(' ','')
                    for y in resultb:
                        if 'WWN' in y and wwna == y.split(':')[1].replace(' ', ''):
                            activeosd(osdname, host, diskx)
                            diskinfo_save(osdname, diskx, None)
                            return None
        else:
            stra = 'Pls check salt service and openattic permissions on salt-master '
            diskinfo_save(osdname, None, stra)
    else:
        stra = 'get disk error, pls try again'
        diskinfo_save(osdname, None, stra)


host = None
osdname = None

try:
    options,args = getopt.getopt(sys.argv[1:],"hp:i:", ["help","osdname=","host="])
except getopt.GetoptError:
    sys.exit()
for name,value in options:
    if name in ("--help"):
        pass
    if name in ("--osdname"):
        osdname=value
    if name in ("--host"):
        host=value

if host is not None and osdname is not None:
    diskstatus(osdname, host)
