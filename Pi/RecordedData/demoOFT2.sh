#!/bin/bash

echo "Demo OFT2 Orbit"

home_dir=$HOME

while read beta1a beta1b beta2a beta2b beta3a beta3b beta4a beta4b psarj ssarj ptrrj strrj v1a v1b v2a v2b v3a v3b v4a v4b sasa_el sasa_az
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
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v1a' where ID = 'S4000001'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v1b' where ID = 'S6000004'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v2a' where ID = 'P4000001'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v2b' where ID = 'P6000004'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v3a' where ID = 'S4000004'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v3b' where ID = 'S6000001'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v4a' where ID = 'P4000004'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$v4b' where ID = 'P6000001'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$sasa_el' where ID = 'S1000005'"
    sqlite3 /dev/shm/iss_telemetry.db "update telemetry set value = '$sasa_az' where ID = 'S1000004'"
done < "$home_dir/Mimic/Pi/RecordedData/demoOFT2.txt"

echo "Finished OFT2 Demo Orbit"
