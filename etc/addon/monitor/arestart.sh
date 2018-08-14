#!/usr/bin/env bash

pida=`ps -ef|grep 'node_exporter_iblock'|grep -v grep|awk -F ' ' '{print $2}'|head -n 1`
pidb=`ps -ef|grep 'node_exporter_iblock'|grep -v grep|awk -F ' ' '{print $2}'`

if [ ! $pida ]
then
    /usr/bin/node_exporter_iblock &
else
    for pid in $pidb
      do
        kill -9 $pidb
      done
    /usr/bin/node_exporter_iblock &
fi
