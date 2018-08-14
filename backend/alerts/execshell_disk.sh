#!/usr/bin/env bash

export PYTHONPATH=/usr/share/openattic

osd=$1
hostname=$2
python2.7 /usr/share/openattic/alerts/diskroam.py --osdname $osd --host $hostname & &> /dev/null &
#python2.7 /usr/share/openattic/alerts/diskroam.py --osdname $osd --host $hostname
