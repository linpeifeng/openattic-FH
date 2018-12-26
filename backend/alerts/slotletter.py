#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
from funclass import Slotletter

slot = Slotletter()

while 1:
    slot.getslot_host()
    slot.getslot_nvme()
    time.sleep(300)
