#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import salt.client
import socket
import os
import sys
import time
sys.path.append("/usr/share/openattic")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from librados import *
from ceph_iscsi.models import *


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
        return ret
    except:
        return 'salt_error'

def iscsiservice(host):
    astr = 'ExecStart=/usr/sbin/lrbd $LRBD_OPTIONS -I\nExecReload=/usr/sbin/lrbd -I'
    iscsistr = 'cat /usr/lib/systemd/system/lrbd.service|grep ' \
               '"ExecStart=/usr/sbin/lrbd $LRBD_OPTIONS" && cat ' \
               '/usr/lib/systemd/system/lrbd.service|grep ' \
               '"ExecReload=/usr/sbin/lrbd"'
    runsalta = salt_cmd(host, 'cmd.run', [iscsistr])
    if runsalta != 'salt_error' and runsalta:
        recode = runsalta[host]['retcode']
        resulta = runsalta[host]['ret']
        if recode == 0:
            if resulta == astr:
                return 'serviceok'
            else:
                return 'serviceno'
        else:
            pass
    else:
        return 'get iscsi service error'

def getrbdname(host, image, pool):
    cstr = "rbd showmapped|grep -v 'id pool         image snap device'" \
           "|grep %s|grep %s" % (image, pool)
    lista = [cstr]
    for act in lista:
        runsalta = salt_cmd(host, 'cmd.run', [act])
        if runsalta != 'salt_error' and runsalta:
            recode = runsalta[host]['retcode']
            resulta = runsalta[host]['ret']
            if recode == 0:
                try:
                    rbdstr = resulta.split(' ')[-1].split('/')[-1]
                except:
                    return 'rbd name format error'
                else:
                    return rbdstr
            else:
                return 'get rbd name error,pls check iscsi ceph '
        else:
            return 'get rbd name: salt master error'

def setcgrop(host, rbdname, wiops=None, riops=None):
    wstr = "if [ -f '/sys/fs/cgroup/blkio/blkio.throttle.write_iops_device' ]; then echo 'ok'; fi;"
    rstr = "if [ -f '/sys/fs/cgroup/blkio/blkio.throttle.read_iops_device' ]; then echo 'ok'; fi;"
    numstr = "lsblk |grep %s|awk -F ' ' '{print $2}'" % (rbdname)
    lista = [wstr, rstr, numstr]
    listb = []
    listc = []
    for act in lista:
        runsalta = salt_cmd(host, 'cmd.run', [act])
        if runsalta != 'salt_error' and runsalta:
            recode = runsalta[host]['retcode']
            resulta = runsalta[host]['ret']
            if recode == 0:
                listb.append(resulta)
            else:
                return 'get iblock error,pls check /sys/fs/cgroup/blkio/blkio.throttle.*_iops_device '
        else:
            return 'get iblock: salt master error'
    if len(listb) > 2 and listb[0] == 'ok' and listb[1] == 'ok' and ':' in listb[2]:
        majmin = str(listb[2])
        wiopssize = 'echo "%s %s" > /sys/fs/cgroup/blkio/blkio.throttle.write_iops_device' % (
        majmin, wiops)
        riopssize = 'echo "%s %s" > /sys/fs/cgroup/blkio/blkio.throttle.read_iops_device' % (
        majmin, riops)
        if wiops is None and riops is None:
            listc = []
        elif wiops is None and riops is not None:
            listc = [riopssize]
        elif riops is None and wiops is not None:
            listc = [wiopssize]
        elif wiops is not None and riops is not None:
            listc = [riopssize, wiopssize]
        if len(listc) > 0:
            for actb in listc:
                runsaltb = salt_cmd(host, 'cmd.run', [actb])
                if runsaltb != 'salt_error' and runsaltb:
                    recodeb = runsaltb[host]['retcode']
                    if recodeb == 0:
                        stra = 'ok'
                    else:
                        stra = 'set rbd_iops error,pls check /sys/fs/cgroup/blkio/blkio.throttle.*_iops_device '
                else:
                    stra = 'set rbd_iops: salt master error'
            return stra
        else:
            pass

def set_rbdiops():
    try:
        getrbds = iSCSITarget.objects.all()
    except:
        pass
    else:
        for x in getrbds:
            gwhostname = getdns(x.portals[0]['hostname'], fullname=1)
            rbdinfo = x.images
            for y in rbdinfo:
                riops = wiops = iopsinfo = None
                imagename = y['name']
                poolname = y['pool']
                dicta = y['settings']
                if dicta.has_key('readiops'):
                    riops = dicta['readiops']
                if dicta.has_key('writeiops'):
                    wiops = dicta['writeiops']
                if dicta.has_key('setiopsinfo'):
                    iopsinfo = dicta['setiopsinfo']

                erstr = False
                try:
                    if 'error' in iopsinfo:
                        erstr = True
                except:
                    erstr = False
                bstr = iscsiservice(gwhostname)
                if bstr == 'serviceok':
                  dstr = getrbdname(gwhostname, imagename, poolname)
                  if 'error' not in dstr:
                      dicta['setiopsinfo'] = setcgrop(gwhostname, dstr, wiops=wiops, riops=riops)
                  else:
                      dicta['setiopsinfo'] = dstr
                elif bstr =='serviceno':
                  dicta['setiopsinfo'] = 'set iops error: pls check system/lrbd.service'
                elif 'error' in bstr:
                    dicta['setiopsinfo'] = bstr
while 1:
    set_rbdiops()
    time.sleep(3)
