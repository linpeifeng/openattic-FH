#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import salt.client
import sys, socket, os

sys.path.append("/usr/share/openattic")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from alerts.models import *
from librados import *
from django.db import transaction

class Slotletter:
    slotdict = {
        "010": "slot9",
        "011": "slot10",
        "012": "slot11",
        "013": "slot12",
        "110": "slot1",
        "111": "slot2",
        "112": "slot3",
        "113": "slot4",
        "114": "slot5",
        "115": "slot6",
        "116": "slot7",
        "117": "slot8"
    }

    def __init__(self):
        pass

    def getdns(self, hostname, fullname=None):
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

    def salt_cmd(self, tgt,
                 fun,
                 arg=(),
                 timeout=30,
                 expr_form='list',
                 ret='',
                 jid='',
                 **kwargs):
        try:
            local = salt.client.LocalClient()
            pub_data = local.run_job(tgt, fun, arg, expr_form, ret, timeout,
                                     jid,
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

    def insrt_disk(self, wwna=None, hosta=None, osda=None, diska=None, solta=None):
        try:
            Disk_Info.objects.create(wwn=wwna, hostname=hosta, osd=osda, disk=diska, solt=solta)
        except:
            return 'insert_error'

    def ceph_conn(self):
        try:
            client = Client()
            if client.connected():
                return client
            else:
                return 'conn_error'
        except:
            return 'conn_error'

    def strsplit(self, str, rid):
        diskinfo = {"wwn": None, "sn": None, "eid": None, "sid": None, "rid":rid}
        try:
            for x in str.replace(' ', '').split('\n'):
                if x.startswith("Enclosure"):
                    diskinfo["eid"] = x.split(":")[1]
                elif x.startswith("SerialNo"):
                    diskinfo["sn"] = x.split(":")[1]
                elif x.startswith("GUID"):
                    diskinfo["wwn"] = x.split(":")[1]
                elif x.startswith("Slot#"):
                    diskinfo["sid"] = x.split(":")[1]
            return diskinfo
        except:
            pass

    def getwnsn_sas3ircu(self, sninfo, host):
        try:
            diskstr = None
            for x in ["0", "1"]:
                execs = "sas3ircu %s display|grep 'Device is a Hard disk' -A13|grep %s -A2 -B10" % (x ,sninfo)
                runsalt = self.salt_cmd(host, 'cmd.run', [execs])
                if runsalt != 'salt_error' and runsalt:
                    retcode = runsalt[host]['retcode']
                    reinfo = runsalt[host]['ret']
                    if retcode == 0 and reinfo is not None:
                        diskstr =  self.strsplit(runsalt[host]['ret'], x)
            if diskstr is None:
                return "null"
            else:
                return diskstr
        except:
            return 'salt master error: sas3ircu display'

    def getslot3108(self, disk, host):
        return disk, host

    def getslot3008(self, disk, host):
        snnum = "smartctl -s on -a -T permissive /dev/%s|grep 'Serial [Nn]umber'|awk '{print $(NF)}'" % (disk)
        try:
            runsalt = self.salt_cmd(host, 'cmd.run', [snnum])
            if runsalt != 'salt_error' and runsalt:
                retcode = runsalt[host]['retcode']
                if retcode == 0:
                    diskstr = self.getwnsn_sas3ircu(runsalt[host]['ret'], host)
                else:
                    return 'run command error: %s' % (snnum)
            else:
                return 'salt master error get slot'
            if 'error' not in diskstr:
                slotid = "%s%s%s" % (diskstr["rid"], diskstr["eid"], diskstr["sid"])
                if self.slotdict.has_key(slotid):
                    return 'Serial Number: %s :: Slot Number: %s**%s' % (diskstr["sn"], self.slotdict[slotid], diskstr["wwn"])
        except:
            return 'get slot error'

    def check_raid(self, host):
        check3008 = "lspci|grep LSI"
        runsalt = self.salt_cmd(host, 'cmd.run', [check3008])
        try:
            if runsalt != 'salt_error' and runsalt:
                retcode = runsalt[host]['retcode']
                retinfo = runsalt[host]['ret']
                if retcode == 0 and "SAS3008" in retinfo:
                    return "3008"
                elif retcode == 0 and "SAS3108" in retinfo:
                    return "3108"
            else:
                return 'salt master error'
        except:
            return "check raid error"

    def getslot_nvme(self):
        conn = self.ceph_conn()
        if conn != 'conn_error':
            hostlist = set()
            for osd in conn.osd_list():
                try:
                    if '-' in osd['host']:
                        nodehost = osd['host'].split('-')[0]
                    else:
                        nodehost = osd['host']
                except:
                    pass
                else:
                    hostlist.add(nodehost)
            for hostx in hostlist:
                hostname = self.getdns(hostx, fullname=1)
                nvmelist = "nvme list|grep /dev/nvm|awk '{print $1\"+\"$2}'"
                runsalta = self.salt_cmd(hostname, 'cmd.run', [nvmelist])
                if runsalta != 'salt_error' and runsalta:
                    retcode = runsalta[hostname]['retcode']
                    restr = runsalta[hostname]['ret'].split("\n")
                    if retcode == 0 and restr:
                        for x in restr:
                            if 'error' not in x and "+" in x:
                                pcien = self.getnvmeslot(
                                    x.split("+")[0].split("/")[-1], hostname)
                                slotinfo = 'Serial Number: %s :: Slot Number: %s' % (x.split("+")[1], pcien)
                                with transaction.atomic():
                                    try:
                                        Disk_Info.objects.get(
                                            wwn=x.split("+")[1]).delete()
                                    except:
                                        pass
                                    finally:
                                        self.insrt_disk(wwna=x.split("+")[1],
                                                        hosta=hostname,
                                                        diska=x.split("+")[0],
                                                        osda="null",
                                                        solta=slotinfo)
                else:
                    pass
            conn.disconnect()
        else:
            pass

    def getnvmeslot(self, name, host):
        slotex = "dmidecode -t slot|grep `ls -l /sys/class/block/|grep %s$|awk -F '/' '{print $(NF-3)}'` -B10|grep Designation|awk '{print $(NF-1)\"+\"$(NF)}'" % (
            name)
        runsalta = self.salt_cmd(host, 'cmd.run', [slotex])
        if runsalta != 'salt_error' and runsalta:
            retcode = runsalta[host]['retcode']
            restr = runsalta[host]['ret']
            if retcode == 0 and restr and "+" in restr:
                return restr
            else:
                return "null"
        else:
            return "null"

    def Getslot(self, disk, host):
        raid_info = self.check_raid(host)
        if raid_info == '3008' and "error" not in raid_info:
            return self.getslot3008(disk, host)
        elif raid_info == '3108' and "error" not in raid_info:
            return self.getslot3108(disk, host)

    def getslot_host(self):
        conn = self.ceph_conn()
        if conn != 'conn_error':
            hoststatus_list = []
            for osd in conn.osd_list():
                try:
                    if '-' in osd['host']:
                        nodehost = osd['host'].split('-')[0]
                    else:
                        nodehost = osd['host']
                except:
                    pass
                else:
                    hoststatus_list.append({osd['host']: osd['status']})
                    osdid = osd['id']
                    comm_df = "lsblk -s|grep ceph-%s$|cut -b 1-3" % (osdid)
                    hostname = self.getdns(nodehost, fullname=1)
                    runsalta = self.salt_cmd(hostname, 'cmd.run', [comm_df])
                    if runsalta != 'salt_error' and runsalta:
                        retcode = runsalta[hostname]['retcode']
                        if retcode == 0 and runsalta[hostname]['ret']:
                            diskb = runsalta[hostname]['ret']
                            stra = self.Getslot(diskb, hostname)
                            if stra is not None and '**' in stra:
                                wwnnum = stra.split('**')[1]
                                slotinfo = stra.split('**')[0]
                            else:
                                wwnnum = None
                                slotinfo = stra
                        else:
                            diskb = 'osd.%s service' % (osdid)
                            #slotinfo = self.Getslot(runsalta[hostname][
                            # 'ret'], hostname)
                        if slotinfo is not None and 'error' not in slotinfo and 'osd' not in diskb:
                            with transaction.atomic():
                                try:
                                    Disk_Info.objects.get(wwn=wwnnum).delete()
                                    Disk_Info.objects.filter(hostname=hostname,
                                                             osd='osd.%s' % (
                                                                 osdid),
                                                             disk=diskb).delete()
                                except:
                                    pass
                                finally:
                                    self.insrt_disk(wwna=wwnnum, hosta=hostname,
                                                    osda='osd.%s' % (osdid),
                                                    diska=diskb,
                                                    solta=slotinfo)
                        elif 'osd' not in diskb:
                            with transaction.atomic():
                                try:
                                    Disk_Info.objects.get(wwn=wwnnum).delete()
                                    Disk_Info.objects.filter(hostname=hostname, osd='osd.%s' % (osdid), disk=diskb).delete()
                                except:
                                    pass
                                finally:
                                    self.insrt_disk(wwna=wwnnum, hosta=hostname, osda='osd.%s' % (osdid), diska=diskb, solta=slotinfo)
                    else:
                        pass
            conn.disconnect()
        else:
            pass
