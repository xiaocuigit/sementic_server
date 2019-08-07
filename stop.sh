#!/bin/bash

count=`ps -ef | grep manage.py | grep -v grep | wc -l`

if [ $count -ne 0 ]
then
    kill -9 `ps -ef | grep manage.py | grep -v "grep"|awk '{print $2}'`
    echo "stop django service success."
else
    echo "django service is not running"
fi
