#!/usr/bin/env python3

from lightstreamer.client import LightstreamerClient, Subscription
import requests
import json

from telemetry_ids import IDENTIFIERS

print(IDENTIFIERS)

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

old_mt_site = -1
old_att_man = -1
old_station_mode = -1
old_pump = -1
old_strrj = -1
old_ptrrj = -1
old_psarj = -1
old_ssarj= -1
old_ssrms_base  = -1
old_lee  = -1
old_spdm_base= -1
old_gnc = -1
old_uhf1 = -1
old_uhf2 = -1
old_iss_mass = -1
old_z1 = -1
old_sm_flag_value = -1
old_kurs_distance = 0
first_update_status = {}

class StatusUpdater:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def onStatusChange(self, newStatus):
        print(f"Client status: {newStatus}")

class MainListener:
    def __init__(self, webhook_url):
        super().__init__()
        self.webhook_url = webhook_url

    def onSubscription(self):
        print("Subscribed!")

    def onUnsubscription(self):
        print("Unsubscribed!")

    def onItemUpdate(self, update):
        global EVAmessagesent, stationmode, Pressuremessage1sent, Pressuremessage1unsent, Pressuremessage2sent, Pressuremessage2unsent, Pressuremessage3sent, Pressuremessage3unsent, firstrun, ptrrj, strrj, first_update_status, ptrrj_prev_values, strrj_prev_values, rs_docking_message
        global old_att_man, old_z1, old_mt_site, old_station_mode, old_pump, old_strrj, old_ptrrj, old_psarj, old_ssarj, old_ssrms_base, old_lee, old_spdm_base, old_gnc, old_uhf1, old_uhf2, old_sm_flag_value, old_kurs_distance

        if firstrun:
            self.send_discord_message("**Telemetry Webhook Active**")
            firstrun = False
       
        def send_message(title, messages):
            self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
            self.send_discord_message(title)
            print(messages)
            if isinstance(messages, str):
                print("str")
                print(messages)
                try:
                    self.send_discord_message(messages)
                except exception as e:
                    print(e)
            elif isinstance(messages, list):
                print("list")
                message = '\n'.join(messages)  # Combine multiple messages into a single string
                print(message)
                self.send_discord_message(message)
            else:
                raise ValueError("Invalid message format. Expected a string or a list of strings.")

           
        item_name = update.getItemName() 
        value = update.getValue("Value")

        # Ignore the first update for each item
        if item_name not in first_update_status:
            first_update_status[item_name] = True
            return

        #Updates on what worksite the MT is at - checked good
        if item_name == "CSAMT000002" and old_mt_site != value:  # mt worksite
            old_mt_site = value
            print("mt worksite")
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
                print("mt value")
                message = str(worksite_messages[int(value)])
                send_message("**ISS Mobile Transporter Alert**",message)

        #Attitude Maneuver - checked good
        elif item_name == "USLAB000081" and old_att_man != value:
            old_att_man = value
            print("attitude maneuver")
            if int(value) == 1:
                send_message("**ISS Attitude Maneuver Alert**", "Attitude Manuever in progress!")
            elif int(value) == 0:
                send_message("**ISS Attitude Maneuver Alert**", "Attitude Manuever complete!")

        #ISS Station Operational modes - checked good
        elif item_name == "USLAB000086" and old_station_mode != value:  # station mode
            old_station_mode = value
            print("station mode")
            station_mode = value
            print(value)
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
                message = mode_messages[int(station_mode)]
                send_message("**ISS Station Mode Change Alert**", message)

        #ISS Cabin Pressure Checks - checked good
        elif item_name == "USLAB000058": #cabin pressure torr
            print("cabin pres")
            cabinpressure = float(value)
            cabinpressurePSI = cabinpressure * 0.0193368
            #range 1: 14 to 14.3 PSI 
            if cabinpressure < 739 and not Pressuremessage1sent:
                send_message("**ISS Pressure Reading - Info**", f"ISS Cabin Pressure is below typical minimum level (threshold is 14.3 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage1sent = True
                leak1 = True
            elif cabinpressure >= 739 and leak1:
                send_message("**ISS Pressure Reading - Pressure Increased**", f"ISS Cabin Pressure is no longer below the typical minimum level (threshold is 14.3 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage1sent = False
                leak1 = False
            #range 2: 10 to 14 PSI
            if cabinpressure < 724.0 and not Pressuremessage2sent:
                send_message("**ISS Pressure Reading - Warning**", f"ISS Cabin Pressure is below nominal minimum level (threshold is 14.0 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage2sent = True
                leak2 = True
            elif cabinpressure >= 724.0 and leak2:
                send_message("**ISS Pressure Reading - Pressure Increased**", f"ISS Cabin Pressure is no longer below the nominal minimum level (threshold is 14.0 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage2sent = False
                leak2 = False
            #range 3: <10 PSI
            if cabinpressure < 500.0 and not Pressuremessage3sent:
                send_message("**ISS Pressure Reading - Potential Emergency**", f"ISS Cabin Pressure has reached the evacuation level (threshold is 10.0 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage3sent = True
                leak3 = True
            elif cabinpressure >= 500.0 and leak3:
                send_message("**ISS Pressure Reading - Pressure Increased**", f"ISS Cabin Pressure is no longer below the evacuation level (threshold is 10.0 PSI) - current pressure is **{cabinpressurePSI:.2f}** PSI")
                Pressuremessage3sent = False
                leak3 = False
               
        #Crewlock pressure - EVA detection - checked good
        elif item_name == "AIRLOCK000049": #crewlock pressure torr
            if float(value) < 600.0 and not EVAmessagesent:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Spacewalk Alert**")
                self.send_discord_message("An EVA (ExtraVehicular Activity - Spacewalk) is about to begin!")
                EVAmessagesent = True
            if EVAmessagesent and float(value) >= 700.0 and EVAmessagesent:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Spacewalk Alert**")
                self.send_discord_message("The EVA has completed!")
                EVAmessagesent = False
        
        #Airlock pump status - checked good
        elif item_name == "AIRLOCK000048" and old_pump != value: #airlock pump
            old_pump = value
            print("airlock pump")
            self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
            self.send_discord_message("**ISS Spacewalk Alert**")
            if int(value) == 1:
                self.send_discord_message("The US Airlock pump is now on! Depress initiated")
            elif int(value) == 0:
                self.send_discord_message("The US Airlock pump is now off!")
        
        #strrj Mode - checked good
        elif item_name == "S0000007" and old_strrj != value:
            old_strrj = value
            print("strrj mode")
            strrj_modes = {1:"STRRJ Mode is now: STANDBY",2:"STRRJ Mode is now: RESTART",3:"STRRJ Mode is now: CHECKOUT",4:"STRRJ Mode is now: DIRECTED_POSITION",5:"STRRJ Mode is now: AUTOTRACK",6:"STRRJ Mode is now: BLIND",7:"STRRJ Mode is now: SHUTDOWN",8:"STRRJ Mode is now: SWITCHOVER"}
            if int(value) in strrj_modes:
                send_message("**ISS Starboard TRRJ Mode Change Alert**", strrj_modes[int(value)])

        #ptrrj Mode - checked good
        elif item_name == "S0000006" and old_ptrrj != value:
            old_ptrrj = value
            print("ptrrj mode")
            ptrrj_modes = {1:"PTRRJ Mode is now: STANDBY",2:"PTRRJ Mode is now: RESTART",3:"PTRRJ Mode is now: CHECKOUT",4:"PTRRJ Mode is now: DIRECTED_POSITION",5:"PTRRJ Mode is now: AUTOTRACK",6:"PTRRJ Mode is now: BLIND",7:"PTRRJ Mode is now: SHUTDOWN",8:"PTRRJ Mode is now: SWITCHOVER"}
            if int(value) in ptrrj_modes:
                send_message("**ISS Port TRRJ Mode Change Alert**", ptrrj_modes[int(value)])

        #PTRRJ value - checked good
        elif item_name == "S0000001": 
            if abs(float(value) - strrj) > 1.0:
                strrj = value
                print("strrj value change")
                message = f"ISS Starboard HRS Radiator Angle is now **{float(value):.2f}**"
                send_message("**ISS STRRJ - Radiator Angle Change**", message)

        #sTRRJ value - checked good
        elif item_name == "S0000002":
            if abs(float(value) - ptrrj) > 1.0:
                ptrrj = value
                print("ptrrj value change")
                message = f"ISS Port HRS Radiator Angle is now **{float(value):.2f}**"
                send_message("**ISS PTRRJ - Radiator Angle Change**", message)

        #PSARJ mode
        elif item_name == "S0000008" and old_psarj != value:
            old_psarj = value
            print("psarj mode")
            psarj_modes = {1:"PSARJ Mode is now: STANDBY",2:"PSARJ Mode is now: RESTART",3:"PSARJ Mode is now: CHECKOUT",4:"PSARJ Mode is now: DIRECTED_POSITION",5:"PSARJ Mode is now: AUTOTRACK",6:"PSARJ Mode is now: BLIND",7:"PSARJ Mode is now: SHUTDOWN",8:"PSARJ Mode is now: SWITCHOVER"}
            if int(value) in psarj_modes:
                send_message("**ISS Port SARJ Mode Change Alert**", psarj_modes[int(value)])
            
        #SSARJ mode
        elif item_name == "S0000009" and old_ssarj != value:
            old_ssarj = value
            print("ssarj mode")
            ssarj_modes = {1:"SSARJ Mode is now: STANDBY",2:"SSARJ Mode is now: RESTART",3:"SSARJ Mode is now: CHECKOUT",4:"SSARJ Mode is now: DIRECTED_POSITION",5:"SSARJ Mode is now: AUTOTRACK",6:"SSARJ Mode is now: BLIND",7:"SSARJ Mode is now: SHUTDOWN",8:"SSARJ Mode is now: SWITCHOVER"}
            if int(value) in ssarj_modes:
                send_message("**ISS Starboard SARJ Mode Change Alert**", ssarj_modes[int(value)])

        #Russion KURS antenna distance (soyuz approaching)
        elif item_name == "RUSSEG000005":
            print("rs vv")
            if float(value) != old_kurs_distance and rs_docking_message is False:
                old_kurs_distance = value
                rs_docking_message = True
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress spacecraft is about to dock!")
            if float(value) == old_kurs_distance:
                rs_docking_message = False
    
        #dc1 docking flag
        elif item_name == "RUSSEG000017":
            print("dc1 mlm? flag")
            if float(value) == 1:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress has just docked with MLM!")

        #mrm1 docking flag
        elif item_name == "RUSSEG000018":
            print("mrm1 flag")
            if float(value) == 1:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress has just docked with MRM-1 (Rassvet)!")
        
        #mrm2 docking flag
        elif item_name == "RUSSEG000019":
            print("mrm2 flag")
            if float(value) == 1:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress has just docked with MRM-2 (Poisk)!")

        #sm docking hooks flag
        elif item_name == "RUSSEG000020":
            print("sm hooks flag")
            if float(value) == 1:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("The Service Module docking hooks are now closed!")

        #sm aft docking flag
        elif item_name == "RUSSEG000014":
            print("sm aft flag")
            if float(value) == 1:
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress has just docked with the Zvezda Service Module Aft Port!")

        #sm docking flag 
        elif item_name == "RUSSEG000012":
            print("sm flag")
            if float(value) == 1 and old_sm_flag_value != value:
                old_sm_flag_value = value
                self.send_discord_message("**~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~**")
                self.send_discord_message("**ISS Visiting Vehicle Alert**")
                self.send_discord_message("A Soyuz/Progress has just docked with the Zvezda Service Module!")

        #SSRMS Base Location - checked good
        elif item_name == "CSASSRMS002" and old_ssrms_base != value:
            old_ssrms_base = value
            print("ssrms base")
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
                message = robotic_operations[int(value)]
                send_message("**ISS SSRMS Base Change**", message)
       
        #SSRMS LEE Status - checked good
        elif item_name == "CSASSRMS011" and old_lee != value:
            old_lee = value
            print("ssrms lee")
            robotic_operations = {
                0: "The SSRMS (Canadarm) has released a payload",
                1: "The SSRMS (Canadarm) has a captive payload",
                2: "The SSRMS (Canadarm) has fully captured the payload"
            }
            if int(value) in robotic_operations:
                message = robotic_operations[int(value)]
                send_message("**ISS SSRMS Status Change**", message)

        #SPDM Base Location - checked good
        elif item_name == "CSASPDM0002" and old_spdm_base != value:
            old_spdm_base = value
            print("spdm base")
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
                message = spdm_bases[int(value)]
                send_message("**ISS SPDM Base Change**", message)
        
        #US GNC mode
        elif item_name == "USLAB000012" and old_gnc != value:
            old_gnc = value
            print("gnc mode")
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
                message = gnc_modes[int(value)]
                send_message("**ISS GN&C Mode Change Alert**", message)

        #UHF1 power
        elif item_name == "USLAB000099" and old_uhf1 != value:
            old_uhf1 = value
            print("uhf1 power")
            uhf1_modes = {
                0:"UHF1 is now Off",
                1:"UHF1 is now On",
                3:"UHF1 is now On (Failed)"
            }
            if int(value) in uhf1_modes:
                message = uhf1_modes[int(value)]
                send_message("**ISS UHF1 Power Status Change**", message)

        #UHF2 power - checked good
        elif item_name == "USLAB000100" and old_uhf2 != value:
            old_uhf2 = value
            print("uhf2 power")
            uhf2_modes = {
                0:"UHF2 is now Off",
                1:"UHF2 is now On",
                3:"UHF2 is now On (Failed)"
            }
            if int(value) in uhf2_modes:
                message = uhf2_modes[int(value)]
                send_message("**ISS UHF2 Power Status Change**", message)
        
        elif item_name == "USLAB000039" and old_iss_mass != value: #ISS mass
            mass_diff = value - old_iss_mass
            old_iss_mass = value
            print("iss mass")
            send_message("**ISS Mass Change Alert**", f"The ISS Reported Mass has increased by **{mass_diff:.2f}** to **{value:.2f}** kilograms!")


    def send_discord_message(self, message):
        payload = {
            "content": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.webhook_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 204:
            print("Failed to send Discord message:", response.text)

def wait_for_input():
    input("{0:-^80}\n".format("Press enter to disconnect & quit."))

def main():
    print('ISS Telemetry script active')
    
    #webhook for test server
    #webhook_url = ""
   
    #webhook for ISS Mimic Discord
    webhook_url = ""

    ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
    ls_client.connectionOptions.setSlowingEnabled(False)

    main_sub = Subscription(mode="MERGE",
        items=IDENTIFIERS,
        fields=["TimeStamp", "Value"])

    status_updater = StatusUpdater(webhook_url)
    main_listener = MainListener(webhook_url)

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


