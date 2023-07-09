#!/bin/bash

echo "Disco Orbit"

home_dir=$HOME

while read beta1a beta1b beta2a beta2b beta3a beta3b beta4a beta4b psarj ssarj ptrrj strrj sasa_el sasa_az
do
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta1a' where ID = 'S4000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta1b' where ID = 'S6000008'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta2a' where ID = 'P4000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta2b' where ID = 'P6000008'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta3a' where ID = 'S4000008'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta3b' where ID = 'S6000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta4a' where ID = 'P4000008'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$beta4b' where ID = 'P6000007'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$psarj' where ID = 'S0000004'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$ssarj' where ID = 'S0000003'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$ptrrj' where ID = 'S0000002'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$strrj' where ID = 'S0000001'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$sasa_el' where ID = 'S1000005'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$sasa_az' where ID = 'S1000004'"
done < "$home_dir/Mimic/Pi/RecordedData/discoOrbit.txt"

echo "Finished Disco Orbit"
