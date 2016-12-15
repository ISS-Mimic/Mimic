The project consists of four parts:

1-3 are on the raspberry pi, 4 is on the arduino mega

1.) The SQL Database (iss_telemetry.db) that houses the most current ISS telemetry values
2.) The Javascript (ISS_Telemetry.js) that subscribes to the lightstreamer server (public client that receives the ISS telemetry from MCC public data adatpers) and updates the SQL database
3.) The graphical user interface (GUI.py) that provides control for the user and manages what data gets sent to the Arduino and displays the status of the telemetry values (connected to live values vs not connected). The GUI retrieves the values from the SQL database and sends them to the arduino if commanded by the user.
4.) The arduino code receives the telemetry values over the serial interface with the raspberry pi and parses the raw data into telemetry specific variables The arduino then commands the motors to turn to the appropriate positions.  
