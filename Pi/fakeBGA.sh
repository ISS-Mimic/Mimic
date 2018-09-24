#!/bin/bash

echo "running"

while read beta
do
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta' where ID = 'P4000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta' where ID = 'P4000008'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta' where ID = 'P6000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta' where ID = 'P6000008'"
done < "bga.txt"
