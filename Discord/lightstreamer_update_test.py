# !/usr/bin/env python3

from lightstreamer.client import LightstreamerClient, Subscription
import requests
import json
import os
from telemetry_ids import IDENTIFIERS
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL

stationmode = 0
EVAmessagesent = False
Pressuremessage1sent = False
Pressuremessage2sent = False
Pressuremessage3sent = False
Pressuremessage1unsent = False
Pressuremessage2unsent = False
Pressuremessage3unsent = False
firstrun = True
ptrrj = 0.0
strrj = 0.0
ptrrj_prev_values = []
strrj_prev_values = []
rs_docking_message = False
last_update = 0.0

first_update_status = {}

telem_data = {
    "CSAMT000002": -1,
    "USLAB000081": -1,
    "USLAB000086": -1,
    "AIRLOCK000048": -1,
    "S0000007": -1,
    "S0000006": -1,
    "S0000008": -1,
    "S0000009": -1,
    "RUSSEG000017": -1,
    "RUSSEG000018": -1,
    "RUSSEG000019": -1,
    "RUSSEG000020": -1,
    "RUSSEG000014": -1,
    "RUSSEG000012": -1,
    "CSASSRMS002": -1,
    "CSASSRMS011": -1,
    "CSASPDM0002": -1,
    "USLAB000012": -1,
    "USLAB000099": -1,
    "USLAB000100": -1,
    "USLAB000039": -1
}

telem_data_updates = {
    "CSAMT000002": 0,
    "USLAB000081": 0,
    "USLAB000086": 0,
    "AIRLOCK000048": 0,
    "S0000007": 0,
    "S0000006": 0,
    "S0000008": 0,
    "S0000009": 0,
    "RUSSEG000017": 0,
    "RUSSEG000018": 0,
    "RUSSEG000019": 0,
    "RUSSEG000020": 0,
    "RUSSEG000014": 0,
    "RUSSEG000012": 0,
    "CSASSRMS002": 0,
    "CSASSRMS011": 0,
    "CSASPDM0002": 0,
    "USLAB000012": 0,
    "USLAB000099": 0,
    "USLAB000100": 0,
    "USLAB000039": 0
}


class StatusUpdater:
    def __init__(self, discord_webhook_url):
        self.discord_webhook_url = discord_webhook_url

    def onStatusChange(self, newStatus):
        print(f"Client status: {newStatus}")


class MainListener:
    def __init__(self, discord_webhook_url):
        super().__init__()
        self.discord_webhook_url = discord_webhook_url

    def onSubscription(self):
        print("Subscribed!")

    def onUnsubscription(self):
        print("Unsubscribed!")

    def onItemUpdate(self, update):
        global EVAmessagesent, stationmode, Pressuremessage1sent, Pressuremessage1unsent, Pressuremessage2sent, Pressuremessage2unsent, Pressuremessage3sent, Pressuremessage3unsent, firstrun, ptrrj, strrj, first_update_status, ptrrj_prev_values, strrj_prev_values
        global telem_data, telem_data_updates, telem_handlers
        global last_update

        
        def getCSAMT000002(value):
            print("in telem message")
            worksite_messages = {
                0: "The ISS Mobile Transporter (MT) is moving - MT Translation in progress!",
                1: "The ISS Mobile Transporter (MT) is now at Worksite #1 (end of the MT rails, starboard side S3 truss)!",
                2: "The ISS Mobile Transporter (MT) is now at Worksite #2!",
                3: "The ISS Mobile Transporter (MT) is now at Worksite #3!",
                4: "The ISS Mobile Transporter (MT) is now at Worksite #4 (home site)!",
                5: "The ISS Mobile Transporter (MT) is now at Worksite #5!",
                6: "The ISS Mobile Transporter (MT) is now at Worksite #6!",
                7: "The ISS Mobile Transporter (MT) is now at Worksite #7!",
                8: "The ISS Mobile Transporter (MT) is now at Worksite #8 (end of the MT rails, port side P3 truss)!"
            }
            if int(value) in worksite_messages:
                message = "**ISS Mobile Transporter Alert** \n"
                message += str(worksite_messages[int(value)])
                message += " \n \n"
                return message
        
        def getUSLAB000081(value):
            print("in telem message")
            if int(value) == 1:
                message = "**ISS Attitude Maneuver Alert** \n"
                message += "Attitude Manuever in progress!"
                message += " \n \n"
            elif int(value) == 0:
                message = "**ISS Attitude Maneuver Alert** \n"
                message += "Attitude Manuever complete!"
                message += " \n \n"
                return message
        
        def getUSLAB000086(value):
            print("in telem message")
            mode_messages = {
                1: [
                    "The ISS has switched to Standard Mode - normal increment operations",
                    "- Power on and activate payload computers",
                    "- Shut down EVA operation support equipment",
                    "- Shut down ARIS",
                    "- Shut down MT"
                ],
                2: [
                    "The ISS has switched to Microgravity Mode - reducing operations that disturb microgravity experiments",
                    "- Shut down space-to-space subsystem radio",
                    "- Start up ARIS",
                    "- Configure GN&C to CMG attitude control mode"
                ],
                4: [
                    "The ISS has switched to Reboost Mode - preparing for ISS reboost operations",
                    "- Configure GN&C to CMG/RCS"
                ],
                8: [
                    "The ISS has switched to Proximity Operations Mode - reconfiguring for a potential visiting spacecraft docking/berthing",
                    "- Supports all nominal rendezvous and departure operations for visiting vehicles",
                    "- Configure space-to-space subsystem radio to orbiter mode",
                    "- Configure GN&C to CMG/RCS assist attitude control mode"
                ],
                16: [
                    "The ISS has switched to External Operations Mode - reconfiguring for EVA/EVR operations",
                    "- Configure space-to-space subsystem radio to EVA mode",
                    "- Configure GN&C to CMG/RCS assist attitude control mode"
                ],
                32: [
                    "The ISS has switched to Survival Mode - reconfiguring for ISS survival in presence of major failure and lack of operator control",
                    "- Loss of critical functions or major failure",
                    "- Shut down user payload support equipment",
                    "- Shut down ARIS",
                    "- Shut down EVA operation support equipment"
                ],
                64: [
                    "The ISS has entered Assured Safe Crew Return Mode - reconfiguring for emergency crew departure",
                    "- Prep for emergency separation and departure of Soyuz/Crew Vehicles",
                    "- Shut down user payload support equipment",
                    "- Shut down ARIS",
                    "- Shut down EVA operation support equipment",
                    "- Configure GN&C to attitude selected for emergency Soyuz departure"
                ]
            }
            if int(station_mode) in mode_messages.keys():
                message = "**ISS Station Mode Change Alert** \n"
                message += mode_messages[int(station_mode)]
                message += " \n \n"
                return message
        
        def getAIRLOCK000048(value):
            print("in telem message")
            if int(value) == 1:
                message = "**ISS Spacewalk Alert** \n"
                message += "The US Airlock pump is now on! Depress initiated"
                message += " \n \n"
                return message
            elif int(value) == 0:
                message = "**ISS Spacewalk Alert** \n"
                message += "The US Airlock pump is now off!"
                message += " \n \n"
                return message

        def getS0000007(value):
            print("in telem message")
            strrj_modes = {1:"STRRJ Mode is now: STANDBY",2:"STRRJ Mode is now: RESTART",3:"STRRJ Mode is now: CHECKOUT",4:"STRRJ Mode is now: DIRECTED_POSITION",5:"STRRJ Mode is now: AUTOTRACK",6:"STRRJ Mode is now: BLIND",7:"STRRJ Mode is now: SHUTDOWN",8:"STRRJ Mode is now: SWITCHOVER"}
            if int(value) in strrj_modes:
                message = "**ISS Starboard TRRJ Mode Change Alert** \n"
                message += strrj_modes[int(value)]
                message += " \n \n"
                return message
        
        def getS0000006(value):
            print("in telem message")
            ptrrj_modes = {1:"PTRRJ Mode is now: STANDBY",2:"PTRRJ Mode is now: RESTART",3:"PTRRJ Mode is now: CHECKOUT",4:"PTRRJ Mode is now: DIRECTED_POSITION",5:"PTRRJ Mode is now: AUTOTRACK",6:"PTRRJ Mode is now: BLIND",7:"PTRRJ Mode is now: SHUTDOWN",8:"PTRRJ Mode is now: SWITCHOVER"}
            if int(value) in ptrrj_modes:
                message = "**ISS Port TRRJ Mode Change Alert** \n"
                message += ptrrj_modes[int(value)]
                message += " \n \n"
                return message
        
        def getS0000008(value):
            print("in telem message")
            psarj_modes = {1:"PSARJ Mode is now: STANDBY",2:"PSARJ Mode is now: RESTART",3:"PSARJ Mode is now: CHECKOUT",4:"PSARJ Mode is now: DIRECTED_POSITION",5:"PSARJ Mode is now: AUTOTRACK",6:"PSARJ Mode is now: BLIND",7:"PSARJ Mode is now: SHUTDOWN",8:"PSARJ Mode is now: SWITCHOVER"}
            if int(value) in psarj_modes:
                message = "**ISS Port SARJ Mode Change Alert** \n"
                message += psarj_modes[int(value)]
                message += " \n \n"
                return message
        
        def getS0000009(value):
            print("in telem message")
            ssarj_modes = {1:"SSARJ Mode is now: STANDBY",2:"SSARJ Mode is now: RESTART",3:"SSARJ Mode is now: CHECKOUT",4:"SSARJ Mode is now: DIRECTED_POSITION",5:"SSARJ Mode is now: AUTOTRACK",6:"SSARJ Mode is now: BLIND",7:"SSARJ Mode is now: SHUTDOWN",8:"SSARJ Mode is now: SWITCHOVER"}
            if int(value) in ssarj_modes:
                message = "**ISS Starboard SARJ Mode Change Alert** \n"
                message += ssarj_modes[int(value)]
                message += " \n \n"
                return message
        
        def getRUSSEG000017(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "A Soyuz/Progress has just docked with MLM (Nauka)!"
                message += " \n \n"
                return message
        
        def getRUSSEG000018(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "A Soyuz/Progress has just docked with MRM-1 (Rassvet)!"
                message += " \n \n"
                return message
        
        def getRUSSEG000019(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "A Soyuz/Progress has just docked with MRM-2 (Poisk)!"
                message += " \n \n"
                return message
        
        def getRUSSEG000020(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "The Russian segment docking hooks are now closed!"
                message += " \n \n"
                return message
        
        def getRUSSEG000014(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "A Soyuz/Progress has just docked with Service Module (Zvezda) Aft!"
                message += " \n \n"
                return message
        
        def getRUSSEG000012(value):
            print("in telem message")
            if float(value) == 1:
                message = "**ISS Visiting Vehicle Alert** \n"
                message += "The Service Module Docking Flag is set!"
                message += " \n \n"
                return message
        
        def getCSASSRMS002(value):
            print("in telem message")
            robotic_operations = {
                1: "The SSRMS (Canadarm) is now attached to the US Lab",
                2: "The SSRMS (Canadarm) is now attached to Node 3",
                4: "The SSRMS (Canadarm) is now attached to Node 2",
                7: "The SSRMS (Canadarm) is now attached to MBS PDGF #1",
                1: "The SSRMS (Canadarm) is now attached to the US Lab",
                2: "The SSRMS (Canadarm) is now attached to Node 3",
                4: "The SSRMS (Canadarm) is now attached to Node 2",
                7: "The SSRMS (Canadarm) is now attached to MBS PDGF #1",
                8: "The SSRMS (Canadarm) is now attached to MBS PDGF #2",
                11: "The SSRMS (Canadarm) is now attached to MBS PDGF #3",
                13: "The SSRMS (Canadarm) is now attached to MBS PDGF #4",
                14: "The SSRMS (Canadarm) is now attached to the FGB",
                16: "The SSRMS (Canadarm) is now attached to the POA",
                19: "The SSRMS (Canadarm) is now attached to SSRMS Tip LEE",
                63: "The SSRMS (Canadarm) is now attached to Undefined"
            }
            if int(value) in robotic_operations:
                message = "**ISS SSRMS Base Change** \n"
                message += robotic_operations[int(value)]
                message += " \n \n"
                return message
        
        def getCSASSRMS011(value):
            print("in telem message")
            robotic_operations = {
                0: "The SSRMS (Canadarm) has released a payload",
                1: "The SSRMS (Canadarm) has a captive payload",
                2: "The SSRMS (Canadarm) has fully captured the payload"
            }
            if int(value) in robotic_operations:
                message = "**ISS SSRMS Status Change** \n"
                message += robotic_operations[int(value)]
                message += " \n \n"
                return message
        
        def getCSASPDM0002(value):
            print("in telem message")
            spdm_bases = {
                1: "The SPDM (Dextre) is now attached to the US Lab",
                2: "The SPDM (Dextre) is now attached to Node 3",
                4: "The SPDM (Dextre) is now attached to Node 2",
                7: "The SPDM (Dextre) is now attached to MBS PDGF #1",
                8: "The SPDM (Dextre) is now attached to MBS PDGF #2",
                11: "The SPDM (Dextre) is now attached to MBS PDGF #3",
                13: "The SPDM (Dextre) is now attached to MBS PDGF #4",
                14: "The SPDM (Dextre) is now attached to the FGB",
                16: "The SPDM (Dextre) is now attached to the POA",
                19: "The SPDM (Dextre) is now attached to SSRMS Tip LEE",
                63: "The SPDM (Dextre) is now attached to Undefined"
            }
            if int(value) in spdm_bases:
                message = "**ISS SPDM Base Change** \n"
                message += spdm_bases[int(value)]
                message += " \n \n"
                return message

        def getUSLAB000012(value):
            print("in telem message")
            gnc_modes = {
                0:"GNC Mode is now: Default",
                1:"GNC Mode is now: WAIT",
                2:"GNC Mode is now: RESERVED",
                3:"GNC Mode is now: STANDBY",
                4:"GNC Mode is now: CMG ATTITUDE CONTROL",
                5:"GNC Mode is now: CMG/THRUSTER ASSIST ATTITUDE CONTROL",
                6:"GNC Mode is now: USER DATA GENERATION",
                7:"GNC Mode is now: FREEDRIFT"
            }
            if int(value) in gnc_modes:
                message = "**ISS GN&C Mode Change Alert** \n"
                message += gnc_modes[int(value)]
                message += " \n \n"
                return message
        
        def getUSLAB000099(value):
            print("in telem message")
            uhf1_modes = {
                0:"UHF1 is now Off",
                1:"UHF1 is now On",
                3:"UHF1 is now On (Failed)"
            }
            if int(value) in uhf1_modes:
                message = "**ISS UHF1 Power Status Change** \n"
                message += uhf1_modes[int(value)]
                message += " \n \n"
                return message
        
        def getUSLAB000100(value):
            print("in telem message")
            uhf2_modes = {
                0:"UHF2 is now Off",
                1:"UHF2 is now On",
                3:"UHF2 is now On (Failed)"
            }
            if int(value) in uhf2_modes:
                message = "**ISS UHF2 Power Status Change** \n"
                message += uhf2_modes[int(value)]
                message += " \n \n"
                return message
        
        def getUSLAB000039(value):
            global telem_data
            print("in telem message")
            old_mass = telem_data["USLAB000039"]
            mass_diff = float(value) - float(old_mass)
        
            message = "**ISS Mass Change Alert** \n"
            message += f"The ISS Reported Mass is now **{float(value):.2f}** kilograms! \n"
            message += f"The mass difference is **{float(mass_diff):.2f}** kilograms!"
            message += " \n \n"
            
            if float(old_mass) == 0.00 or float(value) == 0.00:
                print("server reset - passing mass function")
                return None
            else:
                return message



        # handler functions for each item
        telem_handlers = {
            "CSAMT000002": getCSAMT000002,
            "USLAB000081": getUSLAB000081,
            "USLAB000086": getUSLAB000086,
            "AIRLOCK000048": getAIRLOCK000048,
            "S0000007": getS0000007,
            "S0000006": getS0000006,
            "S0000008": getS0000008,
            "S0000009": getS0000009,
            "RUSSEG000017": getRUSSEG000017,
            "RUSSEG000018": getRUSSEG000018,
            "RUSSEG000019": getRUSSEG000019,
            "RUSSEG000020": getRUSSEG000020,
            "RUSSEG000014": getRUSSEG000014,
            "RUSSEG000012": getRUSSEG000012,
            "CSASSRMS002": getCSASSRMS002,
            "CSASSRMS011": getCSASSRMS011,
            "CSASPDM0002": getCSASPDM0002,
            "USLAB000012": getUSLAB000012,
            "USLAB000099": getUSLAB000099,
            "USLAB000100": getUSLAB000100,
            "USLAB000039": getUSLAB000039
        }

        def send_message(messages):
            try:
                self.send_discord_message(messages)
            except exception as e:
                print(e)

        item_name = update.getItemName()
        value = update.getValue("Value")
        ts = float(update.getValue("TimeStamp"))

        if all(v == 0 for v in telem_data.values()):
            print("all are zero - skipping")
        else:
            if telem_data[item_name] is not None:
                #print(item_name)
                #print(" 1  "+ str(value))
                #print("    "+ str(type(value)))
                #dont send discord messages for first update
                if telem_data_updates[item_name] == 0:
                    telem_data_updates[item_name] = 1
                    #print("    skipping first update")
                else:
                    #print("    not skipping")
                    if telem_data[item_name] != value: 
                        #print("in telem data != value if")
                        #print(ts)
                        #print(str(type(ts)))
                        if ts - last_update > 0: #dontttttt send a meessage unless the value is different from the last and the timestamps arent coming all at once
                            #print("in ts - last update if")
                            message = telem_handlers[item_name](value)
                            telem_data[item_name] = value
                            if message is not None:
                                send_message(message)
                                #print(last_update)
                                #print(ts)
                                print(message)
                            else:
                                print("    message is none")
                                print("    "+str(item_name))
                                print("    "+str(value))
                                print("    "+str(type(value)))
                            last_update = ts
                        else:
                            print("    failed ts check: " + str(ts-last_update))
                    else:
                        print("    failed old value")

        # Overwrite the old data with the newest data
        with open('ISS_data.json', 'w') as f:
            json.dump(telem_data, f)
        

    def send_discord_message(self, message):
        payload = {
            "content": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.discord_webhook_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 204:
            print("Failed to send Discord message:", response.text)


def wait_for_input():
    input("{0:-^80}\n".format("Press enter to disconnect & quit."))


def send_discord_message2(message):
    global discord_webhook_url
    payload = {
        "content": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(discord_webhook_url, data=json.dumps(payload), headers=headers)
    if response.status_code != 204:
        print("Failed to send Discord message:", response.text)

def main():
    global telem_data, discord_webhook_url
    
    #discord_webhook_url = TEST_WEBHOOK_URL
    discord_webhook_url = MIMIC_WEBHOOK_URL
    
    print('ISS Telemetry script active')
    if os.path.exists('ISS_data.json'):
        with open('ISS_data.json', 'r') as f:
            telem_data = json.load(f)
    else:
        with open('ISS_data.json', 'w') as f:
            json.dump(telem_data, f)


    ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
    ls_client.connectionOptions.setSlowingEnabled(False)

    send_discord_message2("Initialized")

    main_sub = Subscription(mode="MERGE",
                            items=IDENTIFIERS,
                            fields=["TimeStamp", "Value"])

    status_updater = StatusUpdater(discord_webhook_url)
    main_listener = MainListener(discord_webhook_url)

    main_sub.addListener(main_listener)
    ls_client.addListener(status_updater)

    ls_client.subscribe(main_sub)

    try:
        ls_client.connect()
        print(ls_client.getStatus())
        wait_for_input()
    finally:
        ls_client.unsubscribe(main_sub)
        ls_client.disconnect()


if __name__ == "__main__":
    main()


