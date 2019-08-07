#!/bin/bash

count=`ps -ef | grep manage.py | grep -v grep | wc -l`

if [ $count -ne 0 ]
then
    echo "django service is running..."
else
    echo "start django service success..."
    python3 manage.py runserver 0.0.0.0:8000 &
fi
