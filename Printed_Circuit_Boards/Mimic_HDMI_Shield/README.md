The HDMI Shield connects directly on top of the motor shields (on top of the microcontroller) and routers the motor power, encoder, and neopixel signals from the microcontroller up the HDMI cables to the HDMI Breakout Board.

The HDMI Shield is a 86mm x 56mm area, 2 layer PCB. The board is designed to be as easy as possible to assemble, but is possible (though expensive) for a PCB company to manufacture with the included Bill of Materials (BOM). 

It is recommended to assemble (solder) the board yourself, it's very straight forward. 

The LEDs and Resistors (small 0603 size surface mount components) are NOT REQUIRED FOR THE BOARD TO FUNCTION. Truly, you can skip those, they are just for watching to see if power is getting to the motors. Just skip these if you are not comfortable with SMT soldering.

The link for the header pins is just for a 40pin strip, just break it off into 1x8 and 1x6 sections. You don't need to connect all the holes in the shield to the pins, only the labelled ones. 

The HDMI connector can be a little hard to find in stock, check ebay/amazon/uxcell and make sure it is that same connector with the pins split up to connector to both sides of the circuit board. Most HDMI connectors have all 19 pins right next to each other and are very difficult to hand solder, these have two rows of pins split up so they are much easier to solder. 

Check for short circuits especially between the HDMI pins and make sure each pin is well soldered to the PCB pad.

Recommended PCB fab shop: JLCPCB, ALLPCB Seeedstudio. All located in China, they are extremely fast, and extremely cheap.

To order a PCB, go to any PCB fab website (they mostly all have the same quote process), enter the 56mm x 86mm for the board area, 2 layers, 1.6mm thickness, and 5x boards quantity. Once it prompts you for to upload the gerber file, upload Mimic_HDMI-edge_Shield_gerber.zip and checkout! That is generally the process for any PCB website.

Those sites also provide the option of assembling (soldering) the components to the PCB for you, but that costs more money and for those hard to find HDMI components you would probably need to ship them some of those or pay for them to procur them. You will need the BOM file for assembly.
