DISCLAIMER - We are not professional programmers. All the code maintained here was created to work toward our specific goal, and much of it was using languages that none of us had used before. You may find the structure, style, and lack of comments to be completely novice and infuriating. You may scream out in frustration, laugh in disgust, or even weep at the obfuscated nonsense appearing before your eyes. 

That said, feel free to improve upon our caffeine-induced, late-night, insanity-plagued programming madness or even just scrap it all and make something better using our ideas.  


The project consists of four parts:

1-3 are on the raspberry pi, 4 is on the arduino mega

1.) The SQL Database (iss_telemetry.db) that houses the most current ISS telemetry values

2.) The Javascript (ISS_Telemetry.js) that subscribes to the lightstreamer server (public client that receives the ISS telemetry from MCC public data adatpers) and updates the SQL database

3.) The graphical user interface (GUI.py) that provides control for the user and manages what data gets sent to the Arduino and displays the status of the telemetry values (connected to live values vs not connected). The GUI retrieves the values from the SQL database and sends them to the arduino if commanded by the user.

4.) The arduino code receives the telemetry values over the serial interface with the raspberry pi and parses the raw data into telemetry specific variables The arduino then commands the motors to turn to the appropriate positions.  


add row to database with

insert into telemetry(one,two,timestamp) values('new row',0.00,0.00);
