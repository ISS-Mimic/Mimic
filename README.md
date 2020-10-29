Welcome to the ISS Mimic project repository! 

![ISS MIMIC!](https://github.com/ISS-Mimic/Mimic/blob/master/Pi/imgs/main/ISSmimicLogoPartsGroundtrack.png)

The International Space Station is constantly downlinking data (telemetry) for Mission Control to monitor. Several years ago, NASA provided some of the data to the public in order to spur interest in the ISS and space exploration under the ISSlive project (https://isslive.com/) using the lightstreamer server (http://demos.lightstreamer.com/ISSLive/). We saw this project and wanted to expand on its potential. Since the development of isslive.com, some more data was added to the public feed and was, sadly, never incorporated into the website. The current total epic and all inclusive list of public telemetry can be seen at our page here https://iss-mimic.github.io/Mimic/ and in an even cooler format here https://iss-mimic.github.io/Mimic/dashboard.html

You can find info on installing our (still heavily in development but with some pretty cool working features now) custom ISS telemetry display program here: https://github.com/ISS-Mimic/Mimic/wiki/Raspberry-Pi---Mimic-Software-Setup-Instructions

The telemetry is awesome in and of itself. But we wanted to do something more with the data, using it to drive software and hardware. Software - running a Raspberry Pi, we want to display all of the telemetry in an interesting and informative manner, enabling visualization of more than just boring numbers. Hardware - using Arduino related microcontrollers, receiving data from the Raspberry Pi, we want to control a 3D-printed model of the ISS and make it exactly match up with the actual ISS in real time. All of the solar arrays, radiators, and outboard truss will be able to rotate to match the ISS joint angles.

![Stuff that moves](http://i.imgur.com/ByhYKrL.png)

The project is still a work in progress. We have a "finished" model that works with all 12 motors turning correctly and able to sync with live data. However, we want to increase the fidelity. And, when it is more mature, we will provide all the STL files and original CAD files to everyone to do whatever they want with them. The software is still a work in progress, too. But from the standpoint of receiving telemetry and transmitting it to the Arduinos, the basic functionality is finished. The finishing touches on the software are all for visualizing the telemetry.

![Functional but not pretty model!](https://i.imgur.com/OlkpRSA.jpg)

DISCLAIMER - We are not professional programmers. We are just a group of dedicated ISS program employees and enthusiasts trying to share our love of the space program through this awesome project. All the code maintained here was created to work toward our specific goal, and much of it was using languages that none of us had used before. You may find the structure, style, and lack of comments to be completely novice and infuriating. You may scream out in frustration, laugh in disgust, or even weep at the obfuscated nonsense appearing before your eyes. 

That said, feel free to improve upon our caffeine-induced, late-night, insanity-plagued programming madness or even just scrap it all and make something better using our ideas.

Check out the wiki for more information.

You can view a video showing some of our project here: https://www.youtube.com/watch?v=sbdHXjDQ-U8

The software is pretty cool and provides even more in-depth functionality than isslive.com. We'll be adding videos and pictures soon to show off the software capabilities.


# Status/Priorities
We are currently focused on refining the CAD model and splitting out all the STL files for printing. All of the STL files currently in this repo are likely outdated or currently changing. We will also release the raw CAD once finished.

We are also working on finishing the software.

Currently working on:
1. Solar Array CAD Redesign 4-Dec-19 (est completion by 12-Dec-2019)
1. Split out all ISS models from Blender model for refinement 4-Dec-19 (est completion by 1-Jan-2020)
1. Improve all software screens/functionality
   1. Orbit Screen Improvements 4-Dec-19 (est completion by 1-Jan-2020)
