# Servo Initialization  [ Preliminary / draft  ]

Prior to installing servos into the model, command them to be in the proper position. 
 *  BGA and SARJs will be set to Zero
 * TRRJs will be set to the middle of it’s rotation range

Steps:

  1.  Connect servo motors to the first 12 ports of PCB
  2.  Label the last two motors “T” for TRRJs.  These two will receive different commands.        ![image](https://github.com/ISS-Mimic/Mimic/assets/58833710/3fca182c-949a-4941-b85a-b19a0a94602a)
  3.  Plug in power supply for Servo PCB
  4.  Upload Arduino code “Mimic Mini”
     
               - int servonum_B1A = 0
               - int servonum_B3A = 1
               - int servonum_B1B = 2
               - int servonum_B3B = 3
          
               - int servonum_B2B = 4
               - int servonum_B4B = 5
               - int servonum_B2A = 6
               - int servonum_B4A = 7
          
               - int servonum_PSARJ = 8
               - int servonum_SSARJ = 9
               - int servonum_PTRRJ = 10
               - int servonum_STRRJ = 11
                 
  5.  Open Arduino Serial Monitor
  6.  Send a special command in the Serial Monitor.
  7.  Disconnect motors for later use.  

# Notes on Lego adapter install
 * Slots in Lego adapter must be “square” with motor, so that SAW will be oriented correctly.  ![image](https://github.com/ISS-Mimic/Mimic/assets/58833710/d1a42a0e-58b4-4c59-9b65-2cc4723c542b)
 * Tweezers can help hold screws for install.  ![image](https://github.com/ISS-Mimic/Mimic/assets/58833710/5e803946-51d8-40e6-b2eb-db48e333c7b6)
 * Servo Extension Cables :
     *   50cm servo extension – TRRJ & SARJ (4 per build)
     *   60cm servo extension – BGAs  (8 per build) – 40 (Options : combined 2x 30cm extensions to create a 60cm extension or use all 60cm cable) 









