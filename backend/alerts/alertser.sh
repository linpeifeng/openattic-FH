#!/usr/bin/env bash


action=$1
export PYTHONPATH=/usr/share/openattic/

####: slotletter
slot_pid=`ps -ef|grep 'slotletter'|grep -v grep|awk -F ' ' '{print $2}'|head -n 1`
slot_pids=`ps -ef|grep 'slotletter'|grep -v grep|awk -F ' ' '{print $2}'`

if [ $1 == 'slotrestart' ]
then
  if [ ! $slot_pid ]
  then
      python2.7 /usr/share/openattic/alerts/slotletter.py &> /dev/null &
  else
      for pid in $slot_pids
        do
          kill -9 $pid &> /dev/null &
        done
      python2.7 /usr/share/openattic/alerts/slotletter.py &> /dev/null &
  fi
fi

if [ $1 == 'slotstop' ]
then
  for pid in $slot_pids
    do
      kill -9 $pid &> /dev/null &
    done
  kill -9 $slot_pid &> /dev/null &
fi

####: setiops
iops_pid=`ps -ef|grep 'setiops.py'|grep -v grep|awk -F ' ' '{print $2}'|head -n 1`
iops_pids=`ps -ef|grep 'setiops.py'|grep -v grep|awk -F ' ' '{print $2}'`

if [ $1 == 'iopsrestart' ]
then
  if [ ! $iops_pid ]
  then
      python2.7 /usr/share/openattic/alerts/setiops.py &> /dev/null &
  else
      for pid in $iops_pids
        do
          kill -9 $pid &> /dev/null &
        done
      python2.7 /usr/share/openattic/alerts/setiops.py &> /dev/null &
  fi
fi

if [ $1 == 'iopsstop' ]
then
  for pid in $iops_pids
    do
      kill -9 $pid &> /dev/null &
    done
  kill -9 $iops_pid &> /dev/null &
fi

####: alert
alert_pid=`ps -ef|grep 'alerts_action.py'|grep -v grep|awk -F ' ' '{print $2}'|head -n 1`
alert_pids=`ps -ef|grep 'alerts_action.py'|grep -v grep|awk -F ' ' '{print $2}'`

if [ $1 == 'alertrestart' ]
then
  if [ ! $alert_pid ]
  then
      python2.7 /usr/share/openattic/alerts/alerts_action.py &> /dev/null &
  else
      for pid in $alert_pids
        do
          kill -9 $pid &> /dev/null &
        done
      python2.7 /usr/share/openattic/alerts/alerts_action.py &> /dev/null &
  fi
fi

if [ $1 == 'alertstop' ]
then
  for pid in $alert_pids
    do
      kill -9 $pid &> /dev/null &
    done
  kill -9 $alert_pid &> /dev/null &
fi
