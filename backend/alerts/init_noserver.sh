#!/usr/bin/env bash

#cd /usr/share/openattic/
#/usr/bin/python2.7 manage.py syncdb

export PYTHONPATH=/usr/share/openattic
/usr/bin/python2.7 /usr/share/openattic/alerts/init_group.py

mv /usr/bin/ceph_exporter /opt/ceph_exporter_backup
cp -a /usr/share/openattic/alerts/ceph_exporter /usr/bin/ceph_exporter
chmod +x /usr/bin/ceph_exporter
systemctl restart prometheus-ceph_exporter.service
