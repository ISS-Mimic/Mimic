[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)
[![Discord](https://img.shields.io/discord/764217406041882684)](https://discord.gg/zPKyE6hBSe)
![GitHub last commit](https://img.shields.io/github/last-commit/ISS-Mimic/Mimic)
[![Twitter Follow](https://img.shields.io/twitter/follow/ISS_Mimic?style=social)](https://twitter.com/ISS_Mimic)
[![YouTube Video Views](https://img.shields.io/youtube/views/W9iZBjzOEEQ?style=social)](https://www.youtube.com/watch?v=W9iZBjzOEEQ)

Welcome to the ISS Mimic project repository! We are developing a 3D printed model of the International Space Station that uses the actual ISS live telemetry to mimic the actual positioning of the ISS solar arrays and radiators! We are also developing tools to visualize all of the ISS public telemetry in informative ways! Join our discord to provide feedback, ask questions, or get involved! 

https://discord.gg/zPKyE6hBSe

We are always looking for people to help with the coding of our raspberry pi telemetry display program, the telemetry website, the creation of ISS CAD models, general project ideas, etc... 

If you want to build your own ISS Mimic, or just want to use the ISS telemetry in your own application, we are more than happy to help. 

Check out our youtube video:

[![ISS MIMIC!](https://img.youtube.com/vi/W9iZBjzOEEQ/0.jpg)](https://www.youtube.com/watch?v=W9iZBjzOEEQ)

![ISS MIMIC!](https://github.com/ISS-Mimic/Mimic/blob/master/Pi/imgs/main/ISSmimicLogoPartsGroundtrack.png)

The International Space Station is constantly downlinking data (telemetry) for Mission Control to monitor. Several years ago, NASA provided some of the data to the public in order to spur interest in the ISS and space exploration under the ISSlive project (https://isslive.com/) using the lightstreamer service (http://demos.lightstreamer.com/ISSLive/). We saw this project and wanted to expand on its potential. Since the development of isslive.com, some more data was added to the public feed and was, sadly, never incorporated into the website. The current total epic and all inclusive list of public telemetry can be seen at our page here https://iss-mimic.github.io/Mimic/ and in an even cooler format here https://iss-mimic.github.io/Mimic/dashboard.html Sadly, ISSlive.com is no longer maintained, but thanks largely in part to our efforts, the telemetry is still being provided to the public through the same lightstreamer connection. 

You can find info on installing our (still heavily in development but with some pretty cool working features now) custom ISS telemetry display program here: https://github.com/ISS-Mimic/Mimic/wiki/Build-Instruction%3A-Mimic-Software-Setup-Instructions

The telemetry is awesome in and of itself. But we wanted to do something more with the data, using it to drive software and hardware. Software - running a Raspberry Pi, we want to display all of the telemetry in an interesting and informative manner, enabling visualization of more than just boring numbers. Hardware - using Arduino related microcontrollers, receiving data from the Raspberry Pi, we want to control a 3D-printed model of the ISS and make it exactly match up with the actual ISS in real time. All of the solar arrays, radiators, and outboard truss will be able to rotate to match the ISS joint angles.

![Stuff that moves](http://i.imgur.com/ByhYKrL.png)

The project is still a work in progress. We have a fully functioning model that works with all 12 motors turning correctly and able to sync with live data. However, we want to increase the fidelity. Our low-fidelity model is completely finished and available here: [STL Files](https://github.com/ISS-Mimic/Mimic/tree/main/3D_Printing). We are still working on the high fidelity upgrade (help us!) and trying to make the ISS look as detailed as possible while still being printable. The software is still a work in progress, too. But from the standpoint of receiving telemetry and transmitting it to the Arduinos, the basic functionality is finished. The finishing touches on the software are all for visualizing the telemetry.

![Functional but not pretty model!](https://i.imgur.com/OlkpRSA.jpg)

DISCLAIMER - We are not professional programmers. We are just a group of dedicated ISS program employees and enthusiasts trying to share our love of the space program through this awesome project. All the code maintained here was created to work toward our specific goal, and much of it was using languages that none of us had used before. You may find the structure, style, and lack of comments to be completely novice and infuriating. You may scream out in frustration, laugh in disgust, or even weep at the obfuscated nonsense appearing before your eyes. 

That said, feel free to improve upon our caffeine-induced, late-night, insanity-plagued programming madness or even just scrap it all and make something better using our ideas.

Check out the wiki for more information.

You can view a video showing some of our project here:https://youtu.be/W9iZBjzOEEQ. Here's an older video: https://www.youtube.com/watch?v=sbdHXjDQ-U8 .

The software is pretty cool and provides even more in-depth functionality than isslive.com. We'll be adding videos and pictures soon to show off the software capabilities.


# Status/Priorities
We are currently focused on refining the CAD model and splitting out all the STL files for printing. All of the STL files currently in this repo are likely outdated or currently changing. We will also release the raw CAD once finished.

We are also working on finishing the software.
