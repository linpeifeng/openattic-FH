#!/usr/bin/env bash

cd /usr/share/openattic/
/usr/bin/python2.7 manage.py syncdb

export PYTHONPATH=/usr/share/openattic
/usr/bin/python2.7 /usr/share/openattic/alerts/init_group.py

rm -rf /etc/openattic/alertsvar.conf
cp -a /usr/share/openattic/alerts/alertsvar.conf /etc/openattic/alertsvar.conf
systemctl restart alertser-systemd.service

rm -rf /usr/lib/python2.7/site-packages/rest_framework/permissions.py
cp -a /usr/share/openattic/alerts/permissions.py /usr/lib/python2.7/site-packages/rest_framework/permissions.py
oaconfig restart

mv /usr/bin/ceph_exporter /opt/ceph_exporter_backup
cp -a /usr/share/openattic/alerts/ceph_exporter /usr/bin/ceph_exporter
chmod +x /usr/bin/ceph_exporter
systemctl restart prometheus-ceph_exporter.service
