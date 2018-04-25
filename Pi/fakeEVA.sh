#!/bin/bash

echo "running"
sleep 10

while read time crew voltage switch air
do
    echo $crew
    echo $air
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$crew' where ID = 'AIRLOCK000049'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000049'"
    
    if [ "$voltage" == 0 ]; then
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$voltage' where ID = 'AIRLOCK000047'"
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000047'"
    fi
    if [ "$voltage" == 1 ]; then
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$voltage' where ID = 'AIRLOCK000047'"
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000047'"
    fi
    if [ "$switch" == 0 ]; then
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$switch' where ID = 'AIRLOCK000048'"
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000048'"
    fi
    if [ "$switch" == 1 ]; then
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$switch' where ID = 'AIRLOCK000048'"
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000048'"
    fi
    if [ "$air" != "-" ]; then
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$air' where ID = 'AIRLOCK000054'"
        sqlite3 /dev/shm/iss_telemetry.db "update telemetry set timestamp = '$time' where ID = 'AIRLOCK000048'"
    fi

    sleep 0.1

done < "TestData.txt"
