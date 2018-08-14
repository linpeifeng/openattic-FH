# -*- coding: utf-8 -*-
import sys
import os
sys.path.append("/usr/share/openattic")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from librados import *


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


def execa(osdname, hostname):
    stra = 'sudo bash /usr/share/openattic/alerts/execshell_disk.sh %s %s' % (osdname, hostname)
    exec_comm(stra)
