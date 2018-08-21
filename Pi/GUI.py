#!/usr/bin/python
import kivy
import urllib2
from bs4 import BeautifulSoup
from calendar import timegm
from datetime import datetime
import pytz
## import reverse_geocode #test1uncomment
import sys
import ephem
import os
import subprocess
import json
import sqlite3
import serial
import time
import sched
import smbus
import math
import random
from threading import Thread
import re
from Naked.toolshed.shell import execute_js, muterun_js
import signal
import multiprocessing
from kivy.network.urlrequest import UrlRequest
from kivy.graphics.svg import Svg
from kivy.animation import Animation
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.popup import Popup 
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.properties import ReferenceListProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.image import Image
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, WipeTransition, SwapTransition
import tweepy
import xml.etree.ElementTree as etree

# Twitter API credentials
consumerKey = ''
consumerSecret = ''
accessToken = ''
accessTokenSecret = ''

# Retrieving key and tokens used for 0Auth
tree = etree.parse('/home/pi/Mimic/Pi/TwitterKeys.xml')
root = tree.getroot()
for child in root:
    if child.tag == 'ConsumerKey' and child.text is not None:
        consumerKey = child.text
        #print("Consumer Key: " + consumerKey)
    elif child.tag == 'ConsumerSecret' and child.text is not None:
        consumerSecret = child.text
        #print("Consumer Secret: " + consumerSecret)
    elif child.tag == 'AccessToken' and child.text is not None:
        accessToken = child.text
        #print("Access Token: " + accessToken)
    elif child.tag == 'AccessTokenSecret' and child.text is not None:
        accessTokenSecret = child.text
        #print("Access Token Secret: " + accessTokenSecret)
    else:
        print("Warning: Unknown or Empty element: " + child.tag)
        print(" Twitter fetching may not work.")

#OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)

# Creation of the actual interface, using authentication
api = tweepy.API(auth)

mimiclog = open('/home/pi/Mimic/Pi/Logs/mimiclog.txt','w')
locationlog = open('/home/pi/Mimic/Pi/Logs/locationlog.txt','a')


#-------------------------Look for a connected arduino-----------------------------------
SerialConnection = False
SerialConnection1 = False
SerialConnection2 = False
SerialConnection3 = False
SerialConnection4 = False

#setting up 2 serial connections to control neopixels and motors seperately 
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
except:
    mimiclog.write(str(datetime.utcnow()))
    mimiclog.write(' ')
    mimiclog.write("Error - serial connection ACM0 not found")
    mimiclog.write('\n')
else:
    SerialConnection1 = True
    ser.write("test")
    mimiclog.write("Error - Successful connection to ")
    mimiclog.write(str(ser))
    print str(ser)

try:
    ser2 = serial.Serial('/dev/ttyACM1', 115200, timeout=0)
except:
    mimiclog.write(str(datetime.utcnow()))
    mimiclog.write(' ')
    mimiclog.write("Error - serial connection ACM1 not found")
    mimiclog.write('\n')
else:
    SerialConnection2 = True
    ser2.write("test")
    mimiclog.write("Error - Successful connection to ")
    mimiclog.write(str(ser2))
    print str(ser2)

try:
    ser3 = serial.Serial('/dev/ttyACM2', 115200, timeout=0)
except:
    mimiclog.write(str(datetime.utcnow()))
    mimiclog.write(' ')
    mimiclog.write("Error - serial connection ACM2 not found")
    mimiclog.write('\n')
else:
    SerialConnection3 = True
    ser.write("test")
    mimiclog.write("Error - Successful connection to ")
    mimiclog.write(str(ser3))
    print str(ser3)

try:
    ser4 = serial.Serial('/dev/ttyAMA00', 115200, timeout=0)
except:
    mimiclog.write(str(datetime.utcnow()))
    mimiclog.write(' ')
    mimiclog.write("Error - serial connection AMA00 not found")
    mimiclog.write('\n')
else:
    SerialConnection4 = True
    ser.write("test")
    mimiclog.write("Error - Successful connection to ")
    mimiclog.write(str(ser4))
    print str(ser4)

#----------------Open SQLITE3 Database that holds the current ISS Telemetry--------------
conn = sqlite3.connect('/dev/shm/iss_telemetry.db')
conn.isolation_level = None
c = conn.cursor() 
c.execute("pragma journal_mode=wal");
c.execute("CREATE TABLE IF NOT EXISTS telemetry (`Label` TEXT PRIMARY KEY, `Timestamp` TEXT, `Value` TEXT, `ID` TEXT, `dbID` NUMERIC )");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('psarj','1216.72738833328','233.039337158203','S0000004',1)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('ssarj','1216.72738833328','126.911819458008','S0000003',2)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('ptrrj','1175.8188055555','-39.9920654296875','S0000002',3)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('strrj','1216.72741666661','25.1238956451416','S0000001',4)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta1b','1216.72669444442','253.663330078125','S6000008',5)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta1a','1216.72669444442','110.802612304688','S4000007',6)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta2b','1216.72724999997','291.62109375','P6000008',7)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta2a','1216.72344388889','345.602416992188','P4000007',8)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta3b','1216.72355444445','194.144897460938','S6000007',9)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta3a','1216.72669444442','249.076538085938','S4000008',10)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta4b','1216.72669444442','69.818115234375','P6000007',11)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('beta4a','1216.7269722222','14.3975830078125','P4000008',12)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('aos','1216.72733833333','1','AOS',13)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('los','7084.92338888884','0','LOS',14)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa1_elevation','1216.7273047222','101.887496948242','S1000005',15)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sgant_elevation','1216.72727777772','105.172134399414','Z1000014',16)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('crewlock_pres','1216.65458361109','754.457946777344','AIRLOCK000049',17)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sgant_xel','1216.72727777772','-38.6938552856445','Z1000015',18)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa1_azimuth','1216.71619333333','185.268753051758','S1000004',19)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopb_flowrate','1216.69486111111','4349.26708984375','P1000001',20)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopb_pressure','1216.72730527778','2162.86865234375','P1000002',21)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopb_temp','1216.72108277778','4.13970804214478','P1000003',22)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopa_flowrate','1216.72683361106','3519.21850585938','S1000001',23)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopa_pressure','1216.70883222222','2103.71728515625','S1000002',24)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('loopa_temp','1216.72386055556','3.63912987709045','S1000003',25)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_1a','1216.72469388889','160.576171875','S4000001',26)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_1b','1216.72480444445','159.49951171875','S6000004',27)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_2a','1216.72422194441','159.90966796875','P4000001',28)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_2b','1216.72433249997','152.73193359375','P6000004',29)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_3a','1216.72469388889','158.78173828125','S4000004',30)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_3b','1216.72480444445','160.986328125','S6000001',31)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_4a','1216.72422194441','158.73046875','P4000004',32)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('voltage_4b','1216.71599916663','159.8583984375','P6000001',33)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_1a','1216.72597222222','-32.1090566730273','S4000002',34)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_1b','1216.72597222222','-65.9772260650065','S6000005',35)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_2a','1216.72574972219','-45.60829685216','P4000002',36)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_2b','1216.72594388889','-30.1572487651965','P6000005',37)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_3a','1216.72597222222','-41.1726404259626','S4000005',38)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_3b','1216.72597222222','-35.8874645656566','S6000002',39)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_4a','1216.72594388889','-44.8238382407841','P4000005',40)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('current_4b','1216.72594388889','-35.2639276439644','P6000002',41)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('kuband_transmit','1216.7250719444','1','Z1000013',42)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('ptrrj_mode','1161.24824999995','4','S0000006',43)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('strrj_mode','1161.24824999995','4','S0000007',44)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('psarj_mode','1160.65219388889','5','S0000008',45)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('ssarj_mode','1160.65219388889','5','S0000009',46)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('russian_mode','1160.65213861108','7','RUSSEG000001',47)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('iss_mode','1160.65419361108','1','USLAB000086',48)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('iss_mass','1161.24836194442','417501.5625','USLAB000039',49)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('us_gnc_mode','1160.65438777778','5','USLAB000012',50)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa2_elevation','1216.7273047222','101.90625','P1000005',51)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa2_azimuth','1216.71572138886','185.268753051758','P1000004',52)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa2_status','1160.66299888889','1','P1000007',53)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('sasa1_status','1160.66066611111','1','S1000009',54)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('active_sasa','1160.66272111111','1','USLAB000092',55)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('position_x','1216.725805','29.8297033276271','USLAB000032',56)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('position_y','1216.725805','5964.89191167363','USLAB000033',57)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('position_z','1216.725805','-3237.06743854422','USLAB000034',58)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('velocity_x','1216.725805','-5433.68688146446','USLAB000035',59)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('velocity_y','1216.725805','-2551.23487465513','USLAB000036',60)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('velocity_z','1216.725805','-4762.70709805804','USLAB000037',61)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU1_VOLTS','1216.69152805554','-0.0286679994314909','AIRLOCK000001',62)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU1_AMPS','1216.69041694442','-0.00489299977198243','AIRLOCK000002',63)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU2_VOLTS','1216.68263916665','-0.0286679994314909','AIRLOCK000003',64)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU2_AMPS','1216.69013916665','-0.00489299977198243','AIRLOCK000004',65)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_IRU_Utility_VOLTS','1216.68238833328','-0.0286679994314909','AIRLOCK000005',66)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('PSA_IRU_Utility_AMPS','1216.7271105555','-0.00489299977198243','AIRLOCK000006',67)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_1_VOLTS','1216.69177749998','-0.0286679994314909','AIRLOCK000007',68)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_1_AMPS','1216.6839997222','-0.00489299977198243','AIRLOCK000008',69)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_2_VOLTS','1216.72705527776','-0.0286679994314909','AIRLOCK000009',70)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_2_AMPS','1216.69122194442','-0.00489299977198243','AIRLOCK000010',71)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_AL1A4A_A_RPC_01_Depress_Pump_On_Off_Stat','1160.66247166667','0','AIRLOCK000047',72)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_Depress_Pump_Power_Switch','1161.24977777772','0','AIRLOCK000048',73)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Hi_P_Supply_Vlv_Actual_Posn','1161.24997194442','0','AIRLOCK000050',74)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Lo_P_Supply_Vlv_Actual_Posn','1161.24997194442','1','AIRLOCK000051',75)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_N2_Supply_Vlv_Actual_Posn','1161.24997194442','1','AIRLOCK000052',76)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_CCAA_State','1161.24994361109','5','AIRLOCK000053',77)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_PCA_Cabin_Pressure','1216.07402833336','752.088439941406','AIRLOCK000054',78)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Hi_P_Supply_Pressure','1216.72674916665','12801.83984375','AIRLOCK000055',79)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Lo_P_Supply_Pressure','1216.72388888889','5624.67041015625','AIRLOCK000056',80)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Airlock_N2_Supply_Pressure','1216.66397138887','11619.3896484375','AIRLOCK000057',81)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node2_MTL_PPA_Avg_Accum_Qty','1161.2497227778','42.8092460632324','NODE2000001',82)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node2_LTL_PPA_Avg_Accum_Qty','1216.72069444444','33.9924049377441','NODE2000002',83)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_2_CCAA_State','1161.24991694444','5','NODE2000003',84)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node2_LTL_TWMV_Out_Temp','1216.72733333336','10.0628938674927','NODE2000006',85)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node2_MTL_TWMV_Out_Temp','1216.694555','17.1698589324951','NODE2000007',86)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppO2','1215.93880527774','171.485071057186','NODE3000001',87)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppN2','1215.93880527774','566.382082394791','NODE3000002',88)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppCO2','1215.93880527774','3.21665350504667','NODE3000003',89)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_UPA_Current_State','1214.98497222225','32','NODE3000004',90)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_UPA_WSTA_Qty_Ctrl_Pct','1216.18163861109','48','NODE3000005',91)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Process_Cmd_Status','1209.33855500003','4','NODE3000006',92)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Process_Step','1209.58580666668','4','NODE3000007',93)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Waste_Water_Qty_Ctrl','1216.72741805553','13.1700000762939','NODE3000008',94)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Water_Storage_Qty_Ctrl','1216.72741805553','82.1500015258789','NODE3000009',95)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_OGA_Process_Cmd_Status','1160.66252694441','1','NODE3000010',96)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_OGA_O2_Production_Rate','1216.72730500003','2.7396981716156','NODE3000011',97)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node3_MTL_TWMV_Out_Temp','1216.69444444444','17.1069641113281','NODE3000012',98)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node3_LTL_TWMV_Out_Temp','1216.59625083334','9.4375','NODE3000013',99)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node3_MTL_PPA_Avg_Accum_Qty','1214.82188833336','78.7650146484375','NODE3000017',100)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node_3_CCAA_State','1161.2465836111','5','NODE3000018',101)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Node3_LTL_PPA_Avg_Accum_Qty','1214.23022166669','59.9398651123047','NODE3000019',102)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_2A_PVCU_On_Off_V_Stat','1161.24858444446','1','P4000003',103)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4A_PVCU_On_Off_V_Stat','1161.24980611112','1','P4000006',104)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4B_RBI_6_Integ_I','0','0','P6000002',105)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4B_PVCU_On_Off_V_Stat','1161.25161166668','1','P6000003',106)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_2B_PVCU_On_Off_V_Stat','1161.24980611112','1','P6000006',107)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS1_On','1161.24980527778','0','RUSSEG000002',108)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS2_On','1161.24980527778','0','RUSSEG000003',109)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_ECW_KURS_Fail','1161.24980527778','0','RUSSEG000004',110)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS_Rng','1161.24991749995','96348.265625','RUSSEG000005',111)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS_Vel','1161.24991749995','134.808670043945','RUSSEG000006',112)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Test_Mode_RS','1161.24980527778','0','RUSSEG000007',113)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Capture_Signal_RS','1161.24980527778','0','RUSSEG000008',114)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Target_Acquisition_Signal_RS','1161.24980527778','0','RUSSEG000009',115)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Functional_Mode_Signal_RS','1161.24980527778','0','RUSSEG000010',116)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_In_Stand_by_Mode_RS','1161.24980527778','0','RUSSEG000011',117)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Dock_Contact','1161.24977833331','0','RUSSEG000012',118)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Forward_Port_Engaged','1161.24977833331','1','RUSSEG000013',119)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Aft_Port_Engaged','1161.24977833331','1','RUSSEG000014',120)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000015',121)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_FGB_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000016',122)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_UDM_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000017',123)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_MRM1_Port_Engaged','1161.24977833331','1','RUSSEG000018',124)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_MRM2_Port_Engaged','1161.24977833331','1','RUSSEG000019',125)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_ETOV_Hooks_Closed','1161.24986222221','0','RUSSEG000020',126)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Act_Att_Ref_Frame','1161.24977833331','1','RUSSEG000021',127)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_RS_Is_Master','1161.24977833331','0','RUSSEG000022',128)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Ready_For_Indicator','1161.24977833331','0','RUSSEG000023',129)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSProp_SM_Thrstr_Mode_Terminated','1161.24983388888','0','RUSSEG000024',130)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_SUDN_Mode','1160.65194444444','6','RUSSEG000025',131)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('SARJ_Port_Commanded_Position','1216.72741666661','233.195175170898','S0000005',132)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S01A_C_RPC_01_Ext_1_MDM_On_Off_Stat','1160.6606108333','1','S0000010',133)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S01A_C_RPC_16_S0_1_MDM_On_Off_Stat','1160.66217666666','1','S0000011',134)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S02B_C_RPC_01_Ext_2_MDM_On_Off_Stat','1160.6606108333','0','S0000012',135)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S02B_C_RPC_16_S0_2_MDM_On_Off_Stat','1160.6606108333','1','S0000013',136)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S11A_C_RPC_03_STR_MDM_On_Off_Stat','1160.66066611111','1','S1000006',137)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S11A_C_RPC_16_S1_1_MDM_On_Off_Stat','1160.66066611111','1','S1000007',138)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S12B_B_RPC_05_S1_2_MDM_On_Off_Stat','1160.66069444444','1','S1000008',139)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_1A_PVCU_On_Off_V_Stat','1161.2484738889','1','S4000003',140)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_3A_PVCU_On_Off_V_Stat','1161.24980611112','1','S4000006',141)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_3B_PVCU_On_Off_V_Stat','1161.2484738889','1','S6000003',142)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('DCSU_1B_PVCU_On_Off_V_Stat','1161.24980611112','1','S6000006',143)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Time of Occurrence','1216.72744333333','4380218418','TIME_000001',144)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Year of Occurrence','1160.65017138885','2018','TIME_000002',145)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG1_Online','1161.24816638887','1','USLAB000001',146)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG2_Online','1161.24816638887','1','USLAB000002',147)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG3_Online','1161.24816638887','1','USLAB000003',148)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG4_Online','1161.24816638887','1','USLAB000004',149)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Num_CMGs_Online','1161.24808277773','4','USLAB000005',150)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_X','1216.72744388892','-2.45458972872734','USLAB000006',151)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_Y','1216.72744388892','4.61879036814499','USLAB000007',152)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_Z','1216.72744388892','-2.27159083915615','USLAB000008',153)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Mag','1216.72736222221','2185.16832879028','USLAB000009',154)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Cap_Pct','1216.72736222221','11.193434715271','USLAB000010',155)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Desat_Request_Inh','1161.25058416665','0','USLAB000011',156)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_AD_Selected_Att_Source','1161.24819611112','1','USLAB000013',157)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_AD_Selected_Rate_Source','1161.24819611112','1','USLAB000014',158)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SD_Selected_State_Source','1161.24850083331','4','USLAB000015',159)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_Att_Cntl_Type','1161.24808277773','1','USLAB000016',160)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_Att_Cntl_Ref_Frame','1160.65273222221','0','USLAB000017',161)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_0','1216.72744416667','0.999212622642517','USLAB000018',162)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_1','1216.72744416667','0.00867813266813755','USLAB000019',163)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_2','1216.72744416667','-0.0168247651308775','USLAB000020',164)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_3','1216.72744416667','-0.0348674207925797','USLAB000021',165)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_X','1216.72741777778','0.368115151294135','USLAB000022',166)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_Y','1216.72741777778','0.0822624275713228','USLAB000023',167)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_Z','1216.72741777778','-0.00235306124983981','USLAB000024',168)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_X','1216.72744416667','0.00437836543317244','USLAB000025',169)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_Y','1216.72744416667','-0.0643700269413879','USLAB000026',170)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_Z','1216.72744416667','0.00107732213344025','USLAB000027',171)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_0_Cmd','1160.65173305551','0.999223709106445','USLAB000028',172)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_1_Cmd','1160.65173305551','0.00549489445984364','USLAB000029',173)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_2_Cmd','1160.65173305551','-0.0176546052098274','USLAB000030',174)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_3_Cmd','1160.65173305551','-0.0347869843244553','USLAB000031',175)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Cap','1216.72466555556','19521.8739049785','USLAB000038',176)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Solar_Beta_Angle','1216.72409416662','-62.734375','USLAB000040',177)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Loss_Of_CMG_Att_Cntl_Latched_Caution','1161.2498047222','0','USLAB000041',178)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CCS_Loss_of_ISS_Attitude_Control_Warning','1161.24986250003','0','USLAB000042',179)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_GPS1_Operational_Status','1216.72222222222','0','USLAB000043',180)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_GPS2_Operational_Status','1216.32369361109','0','USLAB000044',181)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinBrg_Temp1','1216.72562749995','27.6041679382324','USLAB000045',182)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinBrg_Temp1','1216.72573805551','22.6085071563721','USLAB000046',183)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinBrg_Temp1','1216.72237777776','34.7960090637207','USLAB000047',184)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinBrg_Temp1','1216.72579333332','34.8828163146973','USLAB000048',185)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinBrg_Temp2','1216.7223211111','26.1024322509766','USLAB000049',186)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinBrg_Temp2','1216.72573805551','17.3784732818604','USLAB000050',187)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinBrg_Temp2','1216.52016749998','45.776912689209','USLAB000051',188)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinBrg_Temp2','1216.72579333332','33.589412689209','USLAB000052',189)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppO2','1161.24661055558','156.316830573616','USLAB000053',190)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppN2','1161.24661055558','574.227483380585','USLAB000054',191)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppCO2','1160.65574972219','2.2482170546557','USLAB000055',192)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_LTL_PPA_Avg_Accum_Qty','1215.30244388892','79.7446594238281','USLAB000056',193)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_MTL_PPA_Avg_Accum_Qty','1191.26744388892','80.2742004394531','USLAB000057',194)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_PCA_Cabin_Pressure','1216.52375055558','751.785461425781','USLAB000058',195)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB1P6_CCAA_In_T1','1216.71502694441','23.3861961364746','USLAB000059',196)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_MTL_Regen_TWMV_Out_Temp','1216.68211083333','17.2327518463135','USLAB000060',197)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_LTL_TWMV_Out_Temp','1216.70669361108','9.0625','USLAB000061',198)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_VRS_Vent_Vlv_Posn_Raw','1185.75786055558','1','USLAB000062',199)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB_VES_Vent_Vlv_Posn_Raw','1185.70063833336','1','USLAB000063',200)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB1P6_CCAA_State','1161.2465836111','5','USLAB000064',201)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('LAB1S6_CCAA_State','1161.2465836111','4','USLAB000065',202)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_07_CC_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000066',203)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_03_CC_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000067',204)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1A4A_E_RPC_01_CC_3_MDM_On_Off_Stat','1160.66283305552','1','USLAB000068',205)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_09_Int_1_MDM_On_Off_Stat','1160.66283305552','0','USLAB000069',206)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_04_Int_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000070',207)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_11_PL_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000071',208)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD22B_A_RPC_01_PL_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000072',209)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_B_RPC_14_GNC_1_MDM_On_Off_Stat','1160.65444444444','1','USLAB000073',210)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_03_GNC_2_MDM_On_Off_Stat','1160.65447138886','1','USLAB000074',211)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_08_PMCU_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000075',212)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_01_PMCU_2_MDM_On_Off_Stat','1160.66283305552','0','USLAB000076',213)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_B_RPC_09_LAB_1_MDM_On_Off_Stat','1160.66277777778','1','USLAB000077',214)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_04_LAB_2_MDM_On_Off_Stat','1160.66280472219','1','USLAB000078',215)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_13_LAB_3_MDM_On_Off_Stat','1160.66280472219','1','USLAB000079',216)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_D_RPC_01_LAB_FSEGF_Sys_Pwr_1_On_Off_Stat','1160.66280472219','0','USLAB000080',217)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_AttMnvr_In_Progress','1160.65958333333','0','USLAB000081',218)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_Std_Cmd_Accept_Cnt','1216.693305','4089','USLAB000082',219)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_Data_Load_Cmd_Accept_Cnt','1216.05608333336','28711','USLAB000083',220)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Coarse_Time','1216.72722222222','1203093836','USLAB000084',221)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Fine_Time','1216.72747166667','0.59765625','USLAB000085',222)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_PCS_Cnct_Cnt','1171.44763999999','7','USLAB000087',223)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_1_Activity_Indicator','1161.24988833328','1','USLAB000088',224)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_2_Activity_Indicator','1161.24988833328','1','USLAB000089',225)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_3_Activity_Indicator','1161.24988833328','1','USLAB000090',226)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_4_Activity_Indicator','1161.24988833328','1','USLAB000091',227)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Audio_IAC1_Mode_Indication','1161.24972305556','1','USLAB000093',228)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Audio_IAC2_Mode_Indication','1161.24972333332','1','USLAB000094',229)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_9_Source_ID','1166.30116777778','19','USLAB000095',230)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_13_Source_ID','1161.24977888889','28','USLAB000096',231)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_14_Source_ID','1161.24977888889','19','USLAB000097',232)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_29_Source_ID','1161.24977888889','0','USLAB000098',233)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_08_UHF_SSSR_1_On_Off_Stat','1160.66283305552','0','USLAB000099',234)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_H_RPC_04_UHF_SSSR_2_On_Off_Stat','1170.84539000001','0','USLAB000100',235)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('UHF_Frame_Sync','1170.83724944439','0','USLAB000101',236)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SD_Selected_State_Time_Tag','1216.725805','1203093820.00567','USLAB000102',237)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_IG_Vibration','1216.68952833335','0','Z1000001',238)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_IG_Vibration','1216.68958500001','0.006805419921875','Z1000002',239)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_IG_Vibration','1216.68961194442','0.005828857421875','Z1000003',240)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_IG_Vibration','1216.68688944446','0.004364013671875','Z1000004',241)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinMtr_Current','1216.6867788889','0.63671875','Z1000005',242)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinMtr_Current','1216.68961194442','0.5029296875','Z1000006',243)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinMtr_Current','1216.68964027776','1.0947265625','Z1000007',244)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinMtr_Current','1216.68691777779','0.9013671875','Z1000008',245)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_Current_Wheel_Speed','1216.7223211111','6601','Z1000009',246)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_Current_Wheel_Speed','1216.72573805551','6601','Z1000010',247)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_Current_Wheel_Speed','1216.7273886111','6601','Z1000011',248)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_Current_Wheel_Speed','1216.72579333332','6600','Z1000012',249)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('eva_crew_1','0','crew1','0',250)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('eva_crew_2','0','crew2','0',251)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('us_eva_#','0','43','0',252)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('rs_eva_#','0','43','0',253)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('last_us_eva_duration','0','450','0',254)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('last_rs_eva_duration','0','450','0',255)");
c.execute("INSERT OR IGNORE INTO telemetry VALUES('Lightstreamer','0','Unsubscribed','0',0)");

#----------------------------------Variables---------------------------------------------
LS_Subscription = False
overcountry = "None"
isslocationsuccess = False
testfactor = -1
crew_mention= False
crewjsonsuccess = False
mimicbutton = False
fakeorbitboolean = False
zerocomplete = False
switchtofake = False
manualcontrol = False
startup = True
isscrew = 0
different_tweet = False
val = ""
lastsignal = 0
testvalue = 0
obtained_EVA_crew = False
unixconvert = time.gmtime(time.time())
EVAstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
alternate = True       
Beta4Bcontrol = False
Beta3Bcontrol = False
Beta2Bcontrol = False
Beta1Bcontrol = False
Beta4Acontrol = False
Beta3Acontrol = False
Beta2Acontrol = False
Beta1Acontrol = False
PSARJcontrol = False
SSARJcontrol = False
PTRRJcontrol = False
STRRJcontrol = False
stopAnimation = True
startingAnim = True


#-----------EPS Variables----------------------
EPSstorageindex = 0
channel1A_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel1B_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel2A_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel2B_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel3A_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel3B_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel4A_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
channel4B_voltage = [154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1,154.1]
USOS_Power = 0.0
latitude = 0.00
longitude = 0.00
sizeX = 0.00
sizeY = 0.00
psarj2 = 1.0
ssarj2 = 1.0
new_x = 0
new_y = 0
new_x2 = 0
new_y2 = 0
psarj = 0.00
ssarj = 0.00
ptrrj = 0.00
strrj = 0.00
beta1b = 0.00
beta1a = 0.00
beta2b = 0.00
beta2a = 0.00
beta3b = 0.00
beta3a = 0.00
beta4b = 0.00
beta4a = 0.00
beta1b2 = 0.00
beta1a2 = 0.00
beta2b2 = 0.00
beta2a2 = 0.00
beta3b2 = 0.00
beta3a2 = 0.00
beta4b2 = 0.00
beta4a2 = 0.00
aos = 0.00
los = 0.00
seconds2 = 260
timenew = float(time.time())
timeold = 0.00
timenew2 = float(time.time())
timeold2 = 0.00
oldLOS = 0.00
psarjmc = 0.00
ssarjmc = 0.00
ptrrjmc = 0.00
strrjmc = 0.00
beta1bmc = 0.00
beta1amc = 0.00
beta2bmc = 0.00
beta2amc = 0.00
beta3bmc = 0.00
beta3amc = 0.00
beta4bmc = 0.00
beta4amc = 0.00
US_EVAinProgress = False
leak_hold = False
firstcrossing = True
oldAirlockPump = 0.00
position_x = 0.00
position_y = 0.00
position_z = 0.00
velocity_x = 0.00
velocity_y = 0.00
velocity_z = 0.00
velocity = 0.00
altitude = 0.00
mass = 0.00
c1b = 0.00
c1a = 0.00
c3b = 0.00
c3a = 0.00
airlock_pump_voltage = 0
crewlockpres = 758
EVA_activities = False
repress = False
depress = False
seconds = 0
minutes = 0
hours = 0
leak_hold = False
latest_tweet = "No Tweet"
crewmember = ['','','','','','','','','','','','']
crewmemberbio = ['','','','','','','','','','','','']
crewmembertitle = ['','','','','','','','','','','','']
crewmemberdays = ['','','','','','','','','','','','']
crewmemberpicture = ['','','','','','','','','','','','']
crewmembercountry = ['','','','','','','','','','','','']
EV1 = ""
EV2 = ""
numEVAs1 = ""
EVAtime_hours1 = ""
EVAtime_minutes1 = ""
numEVAs2 = ""
EVAtime_hours2 = ""
EVAtime_minutes2 = ""
holdstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
eva = False 
standby = False
prebreath1 = False
prebreath2 = False
depress1 = False
depress2 = False
leakhold = False
repress = False
TLE_acquired = False
stationmode = 0.00

EVA_picture_urls = []
urlindex = 0

internet = False

class MainScreen(Screen):
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]        

    def startBGA(*args):
        global p2
        p2 = subprocess.Popen("/home/pi/Mimic/Pi/fakeBGA.sh")
    
    def stopBGA(*args):
        global p2
        p2.kill()
    
    def startproc(*args):
        global p
        p = subprocess.Popen(["node", "/home/pi/Mimic/Pi/ISS_Telemetry.js"]) 
    
    def killproc(*args):
        global p
        global p2
        try:
            p.kill()
            p2.kill()
        except:
            print "no process"
        os.system('rm /dev/shm/iss_telemetry.db')

class CalibrateScreen(Screen):
    def serialWrite(self, *args):
        ser.write(*args)
        #try:
        #    self.serialActualWrite(self, *args)
        #except:
        #    mimiclog.write(str(datetime.utcnow()))
        #    mimiclog.write(' ')
        #    mimiclog.write("Error - Attempted write - no serial device connected")
        #    mimiclog.write('\n')

    def zeroJoints(self):
        self.changeBoolean(True)
        ser.write('Zero')

    def changeBoolean(self, *args):
        global zerocomplete
        zerocomplete = args[0]

class ManualControlScreen(Screen):
    def setActive(*args):
        global Beta4Bcontrol
        global Beta3Bcontrol
        global Beta2Bcontrol
        global Beta1Bcontrol
        global Beta4Acontrol
        global Beta3Acontrol
        global Beta2Acontrol
        global Beta1Acontrol
        global PSARJcontrol
        global SSARJcontrol
        global PTRRJcontrol
        global STRRJcontrol
        if str(args[1])=="Beta4B":
            Beta4Bcontrol = True
        if str(args[1])=="Beta3B":
            Beta3Bcontrol = True
        if str(args[1])=="Beta2B":
            Beta2Bcontrol = True
        if str(args[1])=="Beta1B":
            Beta1Bcontrol = True
        if str(args[1])=="Beta4A":
            Beta4Acontrol = True
        if str(args[1])=="Beta3A":
            Beta3Acontrol = True
        if str(args[1])=="Beta2A":
            Beta2Acontrol = True
        if str(args[1])=="Beta1A":
            Beta1Acontrol = True
        if str(args[1])=="PTRRJ":
            PTRRJcontrol = True
        if str(args[1])=="STRRJ":
            STRRJcontrol = True
        if str(args[1])=="PSARJ":
            PSARJcontrol = True
        if str(args[1])=="SSARJ":
            SSARJcontrol = True

    def incrementActive(self, *args):
        global Beta4Bcontrol
        global Beta3Bcontrol
        global Beta2Bcontrol
        global Beta1Bcontrol
        global Beta4Acontrol
        global Beta3Acontrol
        global Beta2Acontrol
        global Beta1Acontrol
        global PSARJcontrol
        global SSARJcontrol
        global PTRRJcontrol
        global STRRJcontrol

        if Beta4Bcontrol == True:
            self.incrementBeta4B(args[0])
        if Beta3Bcontrol == True:
            self.incrementBeta3B(args[0])
        if Beta2Bcontrol == True:
            self.incrementBeta2B(args[0])
        if Beta1Bcontrol == True:
            self.incrementBeta1B(args[0])
        if Beta4Acontrol == True:
            self.incrementBeta4A(args[0])
        if Beta3Acontrol == True:
            self.incrementBeta3A(args[0])
        if Beta2Acontrol == True:
            self.incrementBeta2A(args[0])
        if Beta1Acontrol == True:
            self.incrementBeta1A(args[0])
        if PTRRJcontrol == True:
            self.incrementPTRRJ(args[0])
        if STRRJcontrol == True:
            self.incrementSTRRJ(args[0])
        if PSARJcontrol == True:
            self.incrementPSARJ(args[0])
        if SSARJcontrol == True:
            self.incrementSSARJ(args[0])

    def incrementPSARJ(self, *args):
        global psarjmc
        psarjmc += args[1]
        self.serialWrite("PSARJ=" + str(psarjmc) + " ")   
     
    def incrementSSARJ(self, *args):
        global ssarjmc
        ssarjmc += args[1]
        self.serialWrite("SSARJ=" + str(ssarjmc) + " ")   
     
    def incrementPTTRJ(self, *args):
        global ptrrjmc
        ptrrjmc += args[1]
        self.serialWrite("PTRRJ=" + str(ptrrjmc) + " ")   
     
    def incrementSTRRJ(self, *args):
        global strrjmc
        strrjmc += args[1]
        self.serialWrite("STRRJ=" + str(strrjmc) + " ")   
     
    def incrementBeta1B(self, *args):
        global beta1bmc
        beta1bmc += args[1]
        self.serialWrite("Beta1B=" + str(beta1bmc) + " ")   
     
    def incrementBeta1A(self, *args):
        global beta1amc
        beta1amc += args[1]
        self.serialWrite("Beta1A=" + str(beta1amc) + " ")   
     
    def incrementBeta2B(self, *args):
        global beta2bmc
        beta2bmc += args[1]
        self.serialWrite("Beta2B=" + str(beta2bmc) + " ")   
     
    def incrementBeta2A(self, *args):
        global beta2amc
        beta2amc += args[1]
        self.serialWrite("Beta2A=" + str(beta2amc) + " ")   
     
    def incrementBeta3B(self, *args):
        global beta3bmc
        beta3bmc += args[1]
        self.serialWrite("Beta3B=" + str(beta3bmc) + " ")   
     
    def incrementBeta3A(self, *args):
        global beta3amc
        beta3amc += args[1]
        self.serialWrite("Beta3A=" + str(beta3amc) + " ")   
     
    def incrementBeta4B(self, *args):
        global beta4bmc
        beta4bmc += args[1]
        self.serialWrite("Beta4B=" + str(beta4bmc) + " ")   
     
    def incrementBeta4A(self, *args):
        global beta4amc
        beta4amc += args[1]
        self.serialWrite("Beta4A=" + str(beta4amc) + " ")   
     
    def changeBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
    
    def serialWrite(self, *args):
        print args
        ser.write(*args)

class FakeOrbitScreen(Screen):
    def serialWrite(self, *args):
        ser.write(*args)

    def changeBoolean(self, *args):
        global fakeorbitboolean
        global switchtofake
        switchtofake = args[0]
        fakeorbitboolean = args[0]

class Settings_Screen(Screen, EventDispatcher):
    pass

class Orbit_Screen(Screen, EventDispatcher):
    pass

class EPS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])

class CT_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])

class GNC_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])

class EVA_Main_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])
    pass

class EVA_US_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])
    pass

class EVA_RS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])
    pass

class EVA_Pictures(Screen, EventDispatcher):
    pass

class TCS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])

class RS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])
    pass

class Crew_Screen(Screen, EventDispatcher):
    pass

class MimicScreen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1,1,1])
    def changeMimicBoolean(self, *args):
        global mimicbutton
        mimicbutton = args[0]
    
    def changeSwitchBoolean(self, *args):
        global switchtofake
        switchtofake = args[0]
    
    def startBGA(*args):
        global p2
        p2 = subprocess.Popen("/home/pi/Mimic/Pi/fakeBGA.sh")
    
    def stopBGA(*args):
        global p2
        p2.kill()
    
    def startproc(*args):
        global p
        print "mimic starting node"
        p = subprocess.Popen(["node", "/home/pi/Mimic/Pi/ISS_Telemetry.js"]) 

    def killproc(*args):
        global p
        global p2
        global c
        c.execute("INSERT OR IGNORE INTO telemetry VALUES('Lightstreamer','0','Unsubscribed','0',0)");
        try:
            p.kill()
            p2.kill()
        except:
            print "no process"

class MainScreenManager(ScreenManager):
    pass

class MyButton(Button):
    pass

class MainApp(App):

    def build(self):
        global startup
        global crewjsonsuccess
        global stopAnimation
        
        self.main_screen = MainScreen(name = 'main')
        self.calibrate_screen = CalibrateScreen(name = 'calibrate')
        self.control_screen = ManualControlScreen(name = 'manualcontrol')
        self.orbit_screen = Orbit_Screen(name = 'orbit')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.eps_screen = EPS_Screen(name = 'eps')
        self.ct_screen = CT_Screen(name = 'ct')
        self.gnc_screen = GNC_Screen(name = 'gnc')
        self.tcs_screen = TCS_Screen(name = 'tcs')
        self.crew_screen = Crew_Screen(name = 'crew')
        self.settings_screen = Settings_Screen(name = 'settings')
        self.us_eva = EVA_US_Screen(name='us_eva')
        self.rs_eva = EVA_RS_Screen(name='rs_eva')
        self.rs_screen = RS_Screen(name='rs')
        self.eva_main = EVA_Main_Screen(name='eva_main')
        self.eva_pictures = EVA_Pictures(name='eva_pictures')

        root = MainScreenManager(transition=SwapTransition())
        root.add_widget(self.main_screen)
        root.add_widget(self.calibrate_screen)
        root.add_widget(self.control_screen)
        root.add_widget(self.mimic_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(self.orbit_screen)
        root.add_widget(self.eps_screen)
        root.add_widget(self.ct_screen)
        root.add_widget(self.gnc_screen)
        root.add_widget(self.us_eva)
        root.add_widget(self.rs_eva)
        root.add_widget(self.rs_screen)
        root.add_widget(self.eva_main)
        root.add_widget(self.eva_pictures)
        root.add_widget(self.tcs_screen)
        root.add_widget(self.crew_screen)
        root.add_widget(self.settings_screen)
        root.current = 'main' #change this back to main when done with eva setup

        Clock.schedule_interval(self.update_labels, 1)
        Clock.schedule_interval(self.deleteURLPictures, 86400)
        Clock.schedule_interval(self.animate3,0.1)
        Clock.schedule_interval(self.orbitUpdate, 5)
        Clock.schedule_interval(self.checkCrew, 120)
        Clock.schedule_interval(self.checkTwitter, 65) #change back to 65 after testing
        Clock.schedule_interval(self.changePictures, 10)
        if startup == True:
            startup = False

        Clock.schedule_once(self.getTLE, 30)
        Clock.schedule_interval(self.getTLE, 600)
        #Clock.schedule_interval(self.getTLE, 3600)
        Clock.schedule_interval(self.check_internet, 10)
        return root

    def check_internet(self, dt):
        global internet

        def on_success(req, result):
            global internet
            #print "internet success"
            internet = True

        def on_redirect(req, result):
            global internet
            #print "internet redirect"
            internet = True

        def on_failure(req, result):
            global internet
            #print "internet failure"
            internet = False

        def on_error(req, result):
            global internet
            #print "internet error"
            internet = False

        req = UrlRequest("http://google.com", on_success, on_redirect, on_failure, on_error, timeout=1)

    def deleteURLPictures(self, dt):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("deleteURLpictures"))
        mimiclog.write('\n')
        global EVA_picture_urls
        del EVA_picture_urls[:]
        EVA_picture_urls[:] = []

    def changePictures(self, dt):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("changeURLpictures"))
        mimiclog.write('\n')
        global EVA_picture_urls
        global urlindex
        urlsize = len(EVA_picture_urls)
        
        if urlsize > 0:
            self.us_eva.ids.EVAimage.source = EVA_picture_urls[urlindex]
            self.eva_pictures.ids.EVAimage.source = EVA_picture_urls[urlindex]
        
        urlindex = urlindex + 1
        if urlindex > urlsize-1:
            urlindex = 0

    def check_EVA_stats(self,lastname1,firstname1,lastname2,firstname2):                
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("check EVA stats"))
        mimiclog.write('\n')

        global numEVAs1
        global EVAtime_hours1
        global EVAtime_minutes1
        global numEVAs2
        global EVAtime_hours2
        global EVAtime_minutes2
        global EV1
        global EV2

        eva_url = 'http://spacefacts.de/eva/e_eva_az.htm'
        urlthingy = urllib2.urlopen(eva_url)
        soup = BeautifulSoup(urlthingy, 'html.parser')
        
        numEVAs1 = 0
        EVAtime_hours1 = 0
        EVAtime_minutes1 = 0
        numEVAs2 = 0
        EVAtime_hours2 = 0
        EVAtime_minutes2 = 0

        tabletags = soup.find_all("td")
        for tag in tabletags:
            if lastname1 in tag.text:
                if firstname1 in tag.find_next_sibling("td").text:
                    numEVAs1 = tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
                    EVAtime_hours1 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes1 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes1 += (EVAtime_hours1 * 60)

        for tag in tabletags:
            if lastname2 in tag.text:
                if firstname2 in tag.find_next_sibling("td").text:
                    numEVAs2 = tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
                    EVAtime_hours2 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes2 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes2 += (EVAtime_hours2 * 60)
        
        EV1_EVA_number = numEVAs1 
        EV1_EVA_time  = EVAtime_minutes1
        EV2_EVA_number = numEVAs2 
        EV2_EVA_time  = EVAtime_minutes2

        EV1_minutes = str(EV1_EVA_time%60).zfill(2)
        EV2_minutes = str(EV2_EVA_time%60).zfill(2)
        EV1_hours = int(EV1_EVA_time/60)
        EV2_hours = int(EV2_EVA_time/60)

        self.us_eva.ids.EV1.text = str(EV1) + " (EV1):"
        self.us_eva.ids.EV2.text = str(EV2) + " (EV2):"
        self.us_eva.ids.EV1_EVAnum.text = "Number of EVAs = " + str(EV1_EVA_number) 
        self.us_eva.ids.EV2_EVAnum.text = "Number of EVAs = " + str(EV2_EVA_number)
        self.us_eva.ids.EV1_EVAtime.text = "Total EVA Time = " + str(EV1_hours) + "h " + str(EV1_minutes) + "m"
        self.us_eva.ids.EV2_EVAtime.text = "Total EVA Time = " + str(EV2_hours) + "h " + str(EV2_minutes) + "m"

    def checkTwitter(self, dt): #trying to send the twitter stuff to a background thread but I don't know how
        background_thread = Thread(target=self.checkTwitter2)
        background_thread.daemon = True
        background_thread.start()


    def checkTwitter2(self):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("check twitter"))
        mimiclog.write('\n')
        
        global latest_tweet, obtained_EVA_crew, crew_mention, different_tweet, crewmember, crewmemberpicture, numEVAs1, EVAtime_hours1, EVAtime_minutes1, numEVAs2, EVAtime_hours2, EVAtime_minutes2, EV1, EV2

        try:
            stuff = api.user_timeline(screen_name = 'iss101', count = 1, include_rts = True, tweet_mode = 'extended')
            #stuff = api.user_timeline(screen_name = 'iss_mimic', count = 1, include_rts = True, tweet_mode = 'extended')
        except:
            self.us_eva.ids.EVAstatus.text = str("Twitter Error")
            mimiclog.write(str(datetime.utcnow()))
            mimiclog.write(' ')
            mimiclog.write("Error - Tweepy - Error Retrieving Tweet, make sure clock is correct")
            mimiclog.write('\n')
        try:
            stuff
        except NameError:
            print "No tweet - ensure correct time is set"
            self.us_eva.ids.EVAstatus.text = str("Twitter Error")
        else:
            for status in stuff:
                if status.full_text == latest_tweet:
                    different_tweet = False
                else:
                    different_tweet = True

                latest_tweet = status.full_text
                if u'extended_entities' in status._json:
                    if u'media' in status._json[u'extended_entities']:
                        for pic in status._json[u'extended_entities'][u'media']:
                            EVA_picture_urls.append(str(pic[u'media_url']))

        emoji_pattern = re.compile("["u"\U0000007F-\U0001F1FF""]+", flags=re.UNICODE)
        tweet_string_no_emojis = str(emoji_pattern.sub(r'?', latest_tweet)) #cleanse the emojis!!
        self.us_eva.ids.EVAstatus.text = str(tweet_string_no_emojis.split("http",1)[0])

        EVnames = []
        EVpics = []
        index = 0

        if ("EVA BEGINS" in latest_tweet) and latest_tweet.count('@') == 2 and different_tweet:
            crew_mention = True
            while index < len(latest_tweet):
                index = latest_tweet.find('@',index)
                if index == -1:
                    break
                EVnames.append(str(latest_tweet[index:]))
                EVpics.append("")
                index += 1
            count = 0
            while count < len(EVnames):
                EVnames[count] = (EVnames[count].split('@')[1]).split(' ')[0]
                count += 1
            count = 0
            while count < len(EVnames):
                EVpics[count] = str(api.get_user(EVnames[count]).profile_image_url)
                EVnames[count] = str(api.get_user(EVnames[count]).name)
                EVpics[count] = EVpics[count].replace("_normal","_bigger")
                count += 1

        if crew_mention:
            EV1_surname = EVnames[0].split()[-1]
            EV1_firstname = EVnames[0].split()[0]
            #EV1_surname = 'Bresnik'
            EV2_surname = EVnames[1].split()[-1]
            EV2_firstname = EVnames[1].split()[0]
            #EV2_surname = 'Hei'
            EV1 = EVnames[0]
            EV2 = EVnames[1]
            self.us_eva.ids.EV1_Pic.source = str(EVpics[0])
            self.us_eva.ids.EV1_name.text = str(EV1_firstname)
            self.us_eva.ids.EV2_Pic.source = str(EVpics[1])
            self.us_eva.ids.EV2_name.text = str(EV2_firstname)

            background_thread = Thread(target=self.check_EVA_stats, args=(EV1_surname,EV1_firstname,EV2_surname,EV2_firstname))
            background_thread.daemon = True
            background_thread.start()
            #self.check_EVA_stats(EV1_surname,EV2surname)
            obtained_EVA_crew = True 
            crew_mention = False
            
    def checkpasttweets(self):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("check twitter past"))
        mimiclog.write('\n')
        
        global obtained_EVA_crew, crew_mention, different_tweet, crewmember, crewmemberpicture, numEVAs1, EVAtime_hours1, EVAtime_minutes1, numEVAs2, EVAtime_hours2, EVAtime_minutes2, EV1, EV2

        try:
            stuff = api.user_timeline(screen_name = 'iss101', count = 50, include_rts = False, tweet_mode = 'extended')
        except:
            mimiclog.write(str(datetime.utcnow()))
            mimiclog.write(' ')
            mimiclog.write("Error - Tweepy - Error Retrieving Tweet, make sure clock is correct")
            mimiclog.write('\n')
        try:
            stuff
        except NameError:
            print "No tweet - ensure correct time is set"
        else:
            for status in stuff:
                past_tweet = status.full_text

                emoji_pattern = re.compile("["u"\U0000007F-\U0001F1FF""]+", flags=re.UNICODE)
                tweet_string_no_emojis = str(emoji_pattern.sub(r'?', past_tweet)) #cleanse the emojis!!

                EVnames = []
                EVpics = []
                index = 0
                index2 = 0

                if ("EVA BEGINS" in past_tweet) and past_tweet.count('@') == 2:
                    crew_mention = True
                    while index < len(past_tweet):
                        index = past_tweet.find('@',index)
                        index2 = past_tweet.find(',',index2)
                        if index == -1:
                            break
                        if index2 == -1:
                            EVnames.append(str(past_tweet[index:]))
                        else:
                            EVnames.append(str(past_tweet[index:index2]))
                        EVpics.append("")
                        index += 1
                    count = 0
                    while count < len(EVnames):
                        EVnames[count] = (EVnames[count].split('@')[1]).split(' ')[0]
                        count += 1
                    count = 0
                    while count < len(EVnames):
                        try:
                            EVpics[count] = str(api.get_user(EVnames[count]).profile_image_url)
                        except: 
                            print "Twitter EVA crew pic error"
                        else:
                            EVpics[count] = EVpics[count].replace("_normal","_bigger")
                        try:
                            EVnames[count] = str(api.get_user(EVnames[count]).name)
                        except: 
                            print "Twitter EVA name error"
                        count += 1

                if crew_mention:
                    EV1_surname = EVnames[0].split()[-1]
                    EV1_firstname = EVnames[0].split()[0]
                    #EV1_surname = 'Bresnik'
                    EV2_surname = EVnames[1].split()[-1]
                    EV2_firstname = EVnames[1].split()[0]
                    #EV2_surname = 'Hei'
                    EV1 = EVnames[0]
                    EV2 = EVnames[1]
                    self.us_eva.ids.EV1_Pic.source = str(EVpics[0])
                    self.us_eva.ids.EV1_name.text = str(EV1_firstname)
                    self.us_eva.ids.EV2_Pic.source = str(EVpics[1])
                    self.us_eva.ids.EV2_name.text = str(EV2_firstname)

                    background_thread = Thread(target=self.check_EVA_stats, args=(EV1_surname,EV1_firstname,EV2_surname,EV2_firstname))
                    background_thread.daemon = True
                    background_thread.start()
                    #self.check_EVA_stats(EV1_surname,EV2surname)
                    obtained_EVA_crew = True 
                    crew_mention = False
            
    def flashUS_EVAbutton(self, instace):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("flash us eva button"))
        mimiclog.write('\n')

        self.eva_main.ids.US_EVA_Button.background_color = (0,0,1,1)
        def reset_color(*args):
            self.eva_main.ids.US_EVA_Button.background_color = (1,1,1,1)
        Clock.schedule_once(reset_color, 0.5) 

    def flashRS_EVAbutton(self, instace):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("flash rs eva button"))
        mimiclog.write('\n')

        self.eva_main.ids.RS_EVA_Button.background_color = (0,0,1,1)
        def reset_color(*args):
            self.eva_main.ids.RS_EVA_Button.background_color = (1,1,1,1)
        Clock.schedule_once(reset_color, 0.5) 

    def flashEVAbutton(self, instace):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("flash eva button"))
        mimiclog.write('\n')
    
        self.mimic_screen.ids.EVA_button.background_color = (0,0,1,1)
        def reset_color(*args):
            self.mimic_screen.ids.EVA_button.background_color = (1,1,1,1)
        Clock.schedule_once(reset_color, 0.5) 
    
    def EVA_clock(self, dt):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("eva timer"))
        mimiclog.write('\n')
        global seconds
        global minutes
        global hours
        global EVAstartTime
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        difference = (currenthours-EVAstartTime)*3600
        minutes, seconds = divmod(difference, 60)
        hours, minutes = divmod(minutes, 60)

        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)

        self.us_eva.ids.EVA_clock.text =(str(hours) + ":" + str(minutes).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.us_eva.ids.EVA_clock.color = 0.33,0.7,0.18

    def animate(self, instance):
        global new_x2
        global new_y2
        self.main_screen.ids.ISStiny2.size_hint = 0.07,0.07
        new_x2 = new_x2+0.007
        new_y2 = (math.sin(new_x2*30)/18)+0.75
        if new_x2 > 1:
            new_x2 = new_x2-1.0
        self.main_screen.ids.ISStiny2.pos_hint = {"center_x": new_x2, "center_y": new_y2}

    def animate3(self, instance):
        global new_x
        global new_y
        global sizeX
        global sizeY
        global startingAnim
        if new_x<0.886:
            new_x = new_x+0.007
            new_y = (math.sin(new_x*30)/18)+0.75
            self.main_screen.ids.ISStiny.pos_hint = {"center_x": new_x, "center_y": new_y}
        else:
            if sizeX <= 0.15:
                sizeX = sizeX + 0.01
                sizeY = sizeY + 0.01
                self.main_screen.ids.ISStiny.size_hint = sizeX,sizeY
            else:
                if startingAnim:
                    Clock.schedule_interval(self.animate,0.1)
                    startingAnim = False

    def serialWrite(self, *args):
        global SerialConnection1, SerialConnection2, SerialConnection3, SerialConnection4
        
        if SerialConnection1:
            ser.write(*args)
        if SerialConnection2:
            ser2.write(*args)
        if SerialConnection3:
            ser3.write(*args)
        if SerialConnection4:
            ser4.write(*args)
        #try:
        #   ser.write(*args)
        #except:
        #   mimiclog.write(str(datetime.utcnow()))
        #   mimiclog.write(' ')
        #   mimiclog.write("Error - Attempted write - no serial device connected")
        #   mimiclog.write('\n')

    def changeColors(self, *args):   #this function sets all labels on mimic screen to a certain color based on signal status
        #the signalcolor is a kv property that will update all signal status dependant values to whatever color is received by this function 
        self.tcs_screen.signalcolor = args[0],args[1],args[2]
        self.eps_screen.signalcolor = args[0],args[1],args[2]
        self.ct_screen.signalcolor = args[0],args[1],args[2]
        self.orbit_screen.signalcolor = args[0],args[1],args[2]
        self.us_eva.signalcolor = args[0],args[1],args[2]
        self.rs_eva.signalcolor = args[0],args[1],args[2]
        self.eva_main.signalcolor = args[0],args[1],args[2]
        self.mimic_screen.signalcolor = args[0],args[1],args[2]
    
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
       
    def orbitUpdate(self, dt):
        global overcountry, latitude, longitude, tle_rec, line1, line2, TLE_acquired
        if TLE_acquired:
            tle_rec.compute()
            #------------------Latitude/Longitude Stuff---------------------------
            latitude = tle_rec.sublat 
            longitude = tle_rec.sublong
            latitude = float(str(latitude).split(':')[0]) + float(str(latitude).split(':')[1])/60 + float(str(latitude).split(':')[2])/3600
            longitude = float(str(longitude).split(':')[0]) + float(str(longitude).split(':')[1])/60 + float(str(longitude).split(':')[2])/3600
            coordinates = ((latitude,longitude),(latitude,longitude))
            #results = reverse_geocode.search(coordinates)
            #overcountry =  results[0]['country']
            #self.mimic_screen.ids.iss_over_country.text = "The ISS is over " + overcountry
            #converting lat lon to x,y for map
            fromLatSpan = 180.0
            fromLonSpan = 360.0
            toLatSpan = 0.598
            toLonSpan = 0.716
            valueLatScaled = (float(latitude)+90.0)/float(fromLatSpan)
            valueLonScaled = (float(longitude)+180.0)/float(fromLonSpan)
            newLat = (0.265) + (valueLatScaled * toLatSpan) 
            newLon = (0.14) + (valueLonScaled * toLonSpan) 
            self.orbit_screen.ids.OrbitISStiny.pos_hint = {"center_x": newLon, "center_y": newLat}
            self.orbit_screen.ids.latitude.text = str("{:.2f}".format(latitude))
            self.orbit_screen.ids.longitude.text = str("{:.2f}".format(longitude))
            #------------------Orbit Stuff---------------------------
            now = datetime.utcnow() 
            mins = (now - now.replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds()
            orbits_today = math.floor((float(mins)/60)/90)
            self.orbit_screen.ids.dailyorbit.text = str(int(orbits_today)) #display number of orbits since utc midnight
            
            def toYearFraction(date):
                def sinceEpoch(date): # returns seconds since epoch
                    return time.mktime(date.timetuple())
                s = sinceEpoch
                year = date.year
                startOfThisYear = datetime(year=year, month=1, day=1)
                startOfNextYear = datetime(year=year+1, month=1, day=1)
                yearElapsed = s(date) - s(startOfThisYear)
                yearDuration = s(startOfNextYear) - s(startOfThisYear)
                fraction = yearElapsed/yearDuration
                if float(fraction*365.24) < 100:
                    current_epoch = str(date.year)[2:] + "0" + str(fraction*365.24)
                else:
                    current_epoch = str(date.year)[2:] + str(fraction*365.24)
                return current_epoch

            time_since_epoch = float(toYearFraction(datetime.utcnow())) - float(line1[22:36])
            totalorbits = int(line2[68:72]) + 100000 + int(float(time_since_epoch)*24/1.5) #add number of orbits since the tle was generated
            self.orbit_screen.ids.totalorbits.text = str(totalorbits) #display number of orbits since utc midnight
            #------------------ISS Pass Detection---------------------------
            location = ephem.Observer()
            location.lon         = '-95:21:59' #will next to make these an input option
            location.lat         = '29:45:43'
            location.elevation   = 10
            location.name        = 'location'
            location.horizon    = '10'
            location.date = datetime.utcnow()
            tle_rec.compute(location) #compute tle propagation based on provided location
            nextpassinfo = location.next_pass(tle_rec)
            nextpassdatetime = datetime.strptime(str(nextpassinfo[0]),'%Y/%m/%d %H:%M:%S') #convert to datetime object for timezone conversion
            nextpassinfo_format = nextpassdatetime.replace(tzinfo=pytz.utc)
            localtimezone = pytz.timezone('America/Chicago')
            localnextpass = nextpassinfo_format.astimezone(localtimezone)
            self.orbit_screen.ids.iss_next_pass1.text = str(localnextpass).split()[0] #display next pass time
            self.orbit_screen.ids.iss_next_pass2.text = str(localnextpass).split()[1].split('-')[0] #display next pass time

    def getTLE(self, *args):
        #print "inside getTLE"
        global tle_rec, line1, line2, TLE_acquired
        def process_tag_text(tag_text):
            firstTLE = True
            marker = 'TWO LINE MEAN ELEMENT SET'
            text = iter(tag_text.split('\n'))
            for line in text:
                if (marker in line) and firstTLE:
                    firstTLE = False
                    next(text)
                    results.append('\n'.join(
                        (next(text), next(text), next(text))))
            return results
        
        req = urllib2.urlopen('http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html')
        soup = BeautifulSoup(req, 'html.parser')
        body = soup.find_all("pre")
        results = []
        for tag in body:
            if "ISS" in tag.text:
                results.extend(process_tag_text(tag.text))

        if len(results) > 0:
            parsed = str(results[0]).split('\n')
            line1 = parsed[1]
            line2 = parsed[2]
            print line1
            print line2
            tle_rec = ephem.readtle("ISS (ZARYA)",str(line1),str(line2))
            TLE_acquired = True
            print "TLE Success!"
        else:
            print "TLE not acquired"
            TLE_acquired = False

    def updateCrew(self, dt):
        try:
            self.checkCrew(self, *args)
        except:
            mimiclog.write(str(datetime.utcnow()))
            mimiclog.write(' ')
            mimiclog.write("Error - Crew Check - URL Error")
            mimiclog.write('\n')
    
    def checkCrew(self, dt):
        #crew_response = urllib2.urlopen(crew_req)
        global isscrew, crewmember, crewmemberbio, crewmembertitle, crewmemberdays, crewmemberpicture, crewmembercountry
        global internet

        if internet:
            iss_crew_url = 'http://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'        
            req = urllib2.Request(iss_crew_url, headers={'User-Agent' : "Magic Browser"})
            stuff = 0
            try:
                stuff = urllib2.urlopen(req, timeout = 2)
            except:
                mimiclog.write(str(datetime.utcnow()))
                mimiclog.write(' ')
                mimiclog.write("Crew Check - URL Failure")
                mimiclog.write('\n')
           
            now = datetime.utcnow()
            if (stuff.info().getsubtype()=='json'):
                mimiclog.write(str(datetime.utcnow()))
                mimiclog.write(' ')
                mimiclog.write("Crew Check - JSON Success")
                mimiclog.write('\n')
                crewjsonsuccess = True
                data = json.load(stuff)
                number_of_space = int(data['number'])
                for num in range(1,number_of_space+1):
                    if(str(data['people'][num-1]['location']) == str("International Space Station")):
                        crewmember[isscrew] = (data['people'][num-1]['name']).encode('utf-8')
                        crewmemberbio[isscrew] = (data['people'][num-1]['bio'])
                        crewmembertitle[isscrew] = str(data['people'][num-1]['title'])
                        datetime_object = datetime.strptime(str(data['people'][num-1]['launchdate']),'%Y-%m-%d')
                        previousdays = int(data['people'][num-1]['careerdays'])
                        totaldaysinspace = str(now-datetime_object)
                        d_index = totaldaysinspace.index('d')
                        crewmemberdays[isscrew] = str(int(totaldaysinspace[:d_index])+previousdays)+" days in space"
                        crewmemberpicture[isscrew] = str(data['people'][num-1]['biophoto'])
                        crewmembercountry[isscrew] = str(data['people'][num-1]['country']).title()
                        if(str(data['people'][num-1]['country'])==str('usa')):
                            crewmembercountry[isscrew] = str('USA')
                        isscrew = isscrew+1  
            else:
                mimiclog.write(str(datetime.utcnow()))
                mimiclog.write(' ')
                mimiclog.write("Crew Check - JSON Error")
                mimiclog.write('\n')
                crewjsonsuccess = False

        #print crewmemberpicture[0]
        isscrew = 0
        self.crew_screen.ids.crew1.text = crewmember[0]  
        self.crew_screen.ids.crew1title.text = crewmembertitle[0]  
        self.crew_screen.ids.crew1country.text = crewmembercountry[0]  
        self.crew_screen.ids.crew1daysonISS.text = crewmemberdays[0]
        #self.crew_screen.ids.crew1image.source = str(crewmemberpicture[0])
        self.crew_screen.ids.crew2.text = crewmember[1]  
        self.crew_screen.ids.crew2title.text = crewmembertitle[1]  
        self.crew_screen.ids.crew2country.text = crewmembercountry[1]  
        self.crew_screen.ids.crew2daysonISS.text = crewmemberdays[1]
        #self.crew_screen.ids.crew2image.source = str(crewmemberpicture[1])
        self.crew_screen.ids.crew3.text = crewmember[2]  
        self.crew_screen.ids.crew3title.text = crewmembertitle[2]  
        self.crew_screen.ids.crew3country.text = crewmembercountry[2]  
        self.crew_screen.ids.crew3daysonISS.text = crewmemberdays[2]
        #self.crew_screen.ids.crew3image.source = str(crewmemberpicture[2])
        self.crew_screen.ids.crew4.text = crewmember[3]  
        self.crew_screen.ids.crew4title.text = crewmembertitle[3]  
        self.crew_screen.ids.crew4country.text = crewmembercountry[3]  
        self.crew_screen.ids.crew4daysonISS.text = crewmemberdays[3]
        #self.crew_screen.ids.crew4image.source = str(crewmemberpicture[3])
        self.crew_screen.ids.crew5.text = crewmember[4]  
        self.crew_screen.ids.crew5title.text = crewmembertitle[4]  
        self.crew_screen.ids.crew5country.text = crewmembercountry[4]  
        self.crew_screen.ids.crew5daysonISS.text = crewmemberdays[4]
        #self.crew_screen.ids.crew5image.source = str(crewmemberpicture[4])
        self.crew_screen.ids.crew6.text = crewmember[5]  
        self.crew_screen.ids.crew6title.text = crewmembertitle[5]  
        self.crew_screen.ids.crew6country.text = crewmembercountry[5]  
        self.crew_screen.ids.crew6daysonISS.text = crewmemberdays[5]
        #self.crew_screen.ids.crew6image.source = str(crewmemberpicture[5])
        #self.crew_screen.ids.crew7.text = crewmember[6]  
        #self.crew_screen.ids.crew7title.text = crewmembertitle[6]  
        #self.crew_screen.ids.crew7country.text = crewmembercountry[6]  
        #self.crew_screen.ids.crew7daysonISS.text = crewmemberdays[6]
        #self.crew_screen.ids.crew7image.source = str(crewmemberpicture[6])
        #self.crew_screen.ids.crew8.text = crewmember[7]  
        #self.crew_screen.ids.crew8title.text = crewmembertitle[7]  
        #self.crew_screen.ids.crew8country.text = crewmembercountry[7]  
        #self.crew_screen.ids.crew8daysonISS.text = crewmemberdays[7]
        #self.crew_screen.ids.crew8image.source = str(crewmemberpicture[7])
        #self.crew_screen.ids.crew9.text = crewmember[8]  
        #self.crew_screen.ids.crew9title.text = crewmembertitle[8]  
        #self.crew_screen.ids.crew9country.text = crewmembercountry[8]  
        #self.crew_screen.ids.crew9daysonISS.text = crewmemberdays[8]
        #self.crew_screen.ids.crew9image.source = str(crewmemberpicture[8])
        #self.crew_screen.ids.crew10.text = crewmember[9]  
        #self.crew_screen.ids.crew10title.text = crewmembertitle[9]  
        #self.crew_screen.ids.crew10country.text = crewmembercountry[9]  
        #self.crew_screen.ids.crew10daysonISS.text = crewmemberdays[9]
        #self.crew_screen.ids.crew10image.source = str(crewmemberpicture[9])
        #self.crew_screen.ids.crew11.text = crewmember[10]  
        #self.crew_screen.ids.crew11title.text = crewmembertitle[10]  
        #self.crew_screen.ids.crew11country.text = crewmembercountry[10]  
        #self.crew_screen.ids.crew11daysonISS.text = crewmemberdays[10]
        #self.crew_screen.ids.crew11image.source = str(crewmemberpicture[10])
        #self.crew_screen.ids.crew12.text = crewmember[11]  
        #self.crew_screen.ids.crew12title.text = crewmembertitle[11]  
        #self.crew_screen.ids.crew12country.text = crewmembercountry[11]  
        #self.crew_screen.ids.crew12daysonISS.text = crewmemberdays[11]
        #self.crew_screen.ids.crew12image.source = str(crewmemberpicture[11]) 
        
    def map_rotation(self, args):
        scalefactor = 0.083333
        scaledValue = float(args)/scalefactor
        return scaledValue

    def map_psi_bar(self, args):
        scalefactor = 0.015
        scaledValue = (float(args)*scalefactor)+0.72
        return scaledValue
    
    def map_hold_bar(self, args):
        scalefactor = 0.0015
        scaledValue = (float(args)*scalefactor)+0.71
        return scaledValue
    
    def hold_timer(self, dt):
        mimiclog.write(str(datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("hold timer"))
        mimiclog.write('\n')
        global seconds2
        global holdstartTime
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        seconds2 = (currenthours-EVAstartTime)*3600
        seconds2 = int(seconds2)

        new_bar_x = self.map_hold_bar(260-seconds2)
        self.us_eva.ids.leak_timer.text = "~"+ str(int(seconds2)) + "s"
        self.us_eva.ids.Hold_bar.pos_hint = {"center_x": new_bar_x, "center_y": 0.49}
        self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/LeakCheckLights.png'

    def signal_unsubscribed(self): #change images, used stale signal image
        global internet
        if internet == False:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(1,0,0)
        else:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.changeColors(1,0.5,0)
        self.orbit_screen.ids.signal.size_hint_y = 0.112
        self.mimic_screen.ids.signal.size_hint_y = 0.112
        self.eps_screen.ids.signal.size_hint_y = 0.112
        self.ct_screen.ids.signal.size_hint_y = 0.112
        self.tcs_screen.ids.signal.size_hint_y = 0.112
        self.us_eva.ids.signal.size_hint_y = 0.112
        self.rs_screen.ids.signal.size_hint_y = 0.112
    
    def signal_lost(self):
        global internet
        if internet == False:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(1,0,0)
        else:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.changeColors(1,0,0)

        self.orbit_screen.ids.signal.anim_delay = 0.4
        self.mimic_screen.ids.signal.anim_delay = 0.4
        self.eps_screen.ids.signal.anim_delay = 0.4
        self.ct_screen.ids.signal.anim_delay = 0.4
        self.tcs_screen.ids.signal.anim_delay = 0.4
        self.us_eva.ids.signal.anim_delay = 0.4
        self.rs_screen.ids.signal.anim_delay = 0.4
        self.orbit_screen.ids.signal.size_hint_y = 0.112
        self.mimic_screen.ids.signal.size_hint_y = 0.112
        self.eps_screen.ids.signal.size_hint_y = 0.112
        self.ct_screen.ids.signal.size_hint_y = 0.112
        self.tcs_screen.ids.signal.size_hint_y = 0.112
        self.us_eva.ids.signal.size_hint_y = 0.112
        self.rs_screen.ids.signal.size_hint_y = 0.112

    def signal_acquired(self):
        global internet
        if internet == False:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(1,0,0)
        else:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.changeColors(0,1,0)
        self.orbit_screen.ids.signal.anim_delay = 0.05
        self.mimic_screen.ids.signal.anim_delay = 0.05
        self.eps_screen.ids.signal.anim_delay = 0.05
        self.ct_screen.ids.signal.anim_delay = 0.05
        self.tcs_screen.ids.signal.anim_delay = 0.05
        self.us_eva.ids.signal.anim_delay = 0.05
        self.rs_screen.ids.signal.anim_delay = 0.05
        self.orbit_screen.ids.signal.size_hint_y = 0.15
        self.mimic_screen.ids.signal.size_hint_y = 0.15
        self.eps_screen.ids.signal.size_hint_y = 0.15
        self.ct_screen.ids.signal.size_hint_y = 0.15
        self.tcs_screen.ids.signal.size_hint_y = 0.15
        self.us_eva.ids.signal.size_hint_y = 0.15
        self.rs_screen.ids.signal.size_hint_y = 0.15
    
    def signal_stale(self):
        global internet
        if internet == False:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(1,0,0)
        else:
            self.orbit_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.mimic_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.eps_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.ct_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.tcs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.us_eva.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.rs_screen.ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.changeColors(1,0.5,0)
        self.orbit_screen.ids.signal.anim_delay = 0.12
        self.mimic_screen.ids.signal.anim_delay = 0.12
        self.eps_screen.ids.signal.anim_delay = 0.12
        self.ct_screen.ids.signal.anim_delay = 0.12
        self.tcs_screen.ids.signal.anim_delay = 0.12
        self.us_eva.ids.signal.anim_delay = 0.12
        self.rs_screen.ids.signal.anim_delay = 0.12
        self.orbit_screen.ids.signal.size_hint_y = 0.112
        self.mimic_screen.ids.signal.size_hint_y = 0.112
        self.eps_screen.ids.signal.size_hint_y = 0.112
        self.ct_screen.ids.signal.size_hint_y = 0.112
        self.tcs_screen.ids.signal.size_hint_y = 0.112
        self.us_eva.ids.signal.size_hint_y = 0.112
        self.rs_screen.ids.signal.size_hint_y = 0.112

    def update_labels(self, dt):
        global mimicbutton,switchtofake,fakeorbitboolean,psarj2,ssarj2,manualcontrol,psarj,ssarj,ptrrj,strrj,beta1b,beta1a,beta2b,beta2a,beta3b,beta3a,beta4b,beta4a,aos,los,oldLOS,psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1bmc,beta1amc,beta2bmc,beta2amc,beta3bmc,beta3amc,beta4bmc,beta4amc,US_EVAinProgress,position_x,position_y,position_z,velocity_x,velocity_y,velocity_z,altitude,velocity,iss_mass,c1a,c1b,c3a,c3b,testvalue,testfactor,airlock_pump,crewlockpres,leak_hold,firstcrossing,EVA_activities,repress,depress,oldAirlockPump,obtained_EVA_crew,EVAstartTime,beta1a2,beta1b2,beta2a2,beta2b2,beta3a2,beta3b2,beta4a2,beta4b2
        global holdstartTime, LS_Subscription, SerialConnection
        global eva, standby, prebreath1, prebreath2, depress1, depress2, leakhold, repress
        global EPSstorageindex, channel1A_voltage, channel1B_voltage, channel2A_voltage, channel2B_voltage, channel3A_voltage, channel3B_voltage, channel4A_voltage, channel4B_voltage, USOS_Power
        global stationmode

        if SerialConnection1 or SerialConnection2 or SerialConnection3 or SerialConnection4:
            if mimicbutton:
                self.mimic_screen.ids.mimicstartbutton.disabled = True
            else:
                self.mimic_screen.ids.mimicstartbutton.disabled = False
        else:
            self.mimic_screen.ids.mimicstartbutton.disabled = True
            self.mimic_screen.ids.mimicstopbutton.disabled = True

        c.execute('select Value from telemetry')
        values = c.fetchall()
        c.execute('select Timestamp from telemetry')
        timestamps = c.fetchall()
         
        sub_status = str((values[255])[0]) #lightstreamer subscript checker
        if sub_status == "Subscribed":
            LS_Subscription = True
        else:
            LS_Subscription = False
        
        psarj = "{:.2f}".format(float((values[0])[0]))
        if switchtofake == False:
            psarj2 = float(psarj)
        if manualcontrol == False:
            psarjmc = float(psarj)
        ssarj = "{:.2f}".format(float((values[1])[0]))
        if switchtofake == False:
            ssarj2 = float(ssarj)
        if manualcontrol == False:
            ssarjmc = float(ssarj)
        ptrrj = "{:.2f}".format(float((values[2])[0]))
        if manualcontrol == False:
            ptrrjmc = float(ptrrj)
        strrj = "{:.2f}".format(float((values[3])[0]))
        if manualcontrol == False:
            strrjmc = float(strrj)
        beta1b = "{:.2f}".format(float((values[4])[0]))
        if switchtofake == False:
            beta1b2 = float(beta1b)
        if manualcontrol == False:
            beta1bmc = float(beta1b)
        beta1a = "{:.2f}".format(float((values[5])[0]))
        if switchtofake == False:
            beta1a2 = float(beta1a)
        if manualcontrol == False:
            beta1amc = float(beta1a)
        beta2b = "{:.2f}".format(float((values[6])[0]))
        if switchtofake == False:
            beta2b2 = float(beta2b) #+ 20.00
        if manualcontrol == False:
            beta2bmc = float(beta2b)
        beta2a = "{:.2f}".format(float((values[7])[0]))
        if switchtofake == False:
            beta2a2 = float(beta2a)
        if manualcontrol == False:
            beta2amc = float(beta2a)
        beta3b = "{:.2f}".format(float((values[8])[0]))
        if switchtofake == False:
            beta3b2 = float(beta3b)
        if manualcontrol == False:
            beta3bmc = float(beta3b)
        beta3a = "{:.2f}".format(float((values[9])[0]))
        if switchtofake == False:
            beta3a2 = float(beta3a)
        if manualcontrol == False:
            beta3amc = float(beta3a)
        beta4b = "{:.2f}".format(float((values[10])[0]))
        if switchtofake == False:
            beta4b2 = float(beta4b)
        if manualcontrol == False:
            beta4bmc = float(beta4b)
        beta4a = "{:.2f}".format(float((values[11])[0]))
        if switchtofake == False:
            beta4a2 = float(beta4a) #+ 20.00
        if manualcontrol == False:
            beta4amc = float(beta4a)
        aos = "{:.2f}".format(int((values[12])[0]))
        los = "{:.2f}".format(int((values[13])[0]))      
        sasa_el = "{:.2f}".format(float((values[14])[0]))
        sgant_el = "{:.2f}".format(float((values[15])[0]))
        difference = float(sgant_el)-float(sasa_el) 
        v1a = "{:.2f}".format(float((values[25])[0]))
        channel1A_voltage[EPSstorageindex] = float(v1a)
        v1b = "{:.2f}".format(float((values[26])[0]))
        channel1B_voltage[EPSstorageindex] = float(v1b)
        v2a = "{:.2f}".format(float((values[27])[0]))
        channel2A_voltage[EPSstorageindex] = float(v2a)
        v2b = "{:.2f}".format(float((values[28])[0]))
        channel2B_voltage[EPSstorageindex] = float(v2b)
        v3a = "{:.2f}".format(float((values[29])[0]))
        channel3A_voltage[EPSstorageindex] = float(v3a)
        v3b = "{:.2f}".format(float((values[30])[0]))
        channel3B_voltage[EPSstorageindex] = float(v3b)
        v4a = "{:.2f}".format(float((values[31])[0]))
        channel4A_voltage[EPSstorageindex] = float(v4a)
        v4b = "{:.2f}".format(float((values[32])[0]))
        channel4B_voltage[EPSstorageindex] = float(v4b)
        c1a = "{:.2f}".format(float((values[33])[0]))
        c1b = "{:.2f}".format(float((values[34])[0]))
        c2a = "{:.2f}".format(float((values[35])[0]))
        c2b = "{:.2f}".format(float((values[36])[0]))
        c3a = "{:.2f}".format(float((values[37])[0]))
        c3b = "{:.2f}".format(float((values[38])[0]))
        c4a = "{:.2f}".format(float((values[39])[0]))
        c4b = "{:.2f}".format(float((values[40])[0]))
        
        stationmode = float((values[46])[0]) #russian segment mode same as usos mode
        
        quaternion0 = (values[171])[0]
        quaternion1 = (values[172])[0]
        quaternion2 = (values[173])[0]
        quaternion3 = (values[174])[0]

        print quaternion0
        print quaternion1
        print quaternion2
        print quaternion3
        
        ##US EPS Stuff---------------------------##
        solarbeta = "{:.2f}".format(float((values[176])[0]))
        
        power_1a = float(v1a) * float(c1a)
        power_1b = float(v1b) * float(c1b)
        power_2a = float(v2a) * float(c2a)
        power_2b = float(v2b) * float(c2b)
        power_3a = float(v3a) * float(c3a)
        power_3b = float(v3b) * float(c3b)
        power_4a = float(v4a) * float(c4a)
        power_4b = float(v4b) * float(c4b)
        
        USOS_Power = power_1a + power_1b + power_2a + power_2b + power_3a + power_3b + power_4a + power_4b
        self.eps_screen.ids.usos_power.text = str("{:.0f}".format(USOS_Power*-1.0)) + " W"
        self.eps_screen.ids.solarbeta.text = str(solarbeta)

        avg_total_voltage = (float(v1a)+float(v1b)+float(v2a)+float(v2b)+float(v3a)+float(v3b)+float(v4a)+float(v4b))/8.0

        avg_1a = (channel1A_voltage[0]+channel1A_voltage[1]+channel1A_voltage[2]+channel1A_voltage[3]+channel1A_voltage[4]+channel1A_voltage[5]+channel1A_voltage[6]+channel1A_voltage[7]+channel1A_voltage[8]+channel1A_voltage[9])/10
        avg_1b = (channel1B_voltage[0]+channel1B_voltage[1]+channel1B_voltage[2]+channel1B_voltage[3]+channel1B_voltage[4]+channel1B_voltage[5]+channel1B_voltage[6]+channel1B_voltage[7]+channel1B_voltage[8]+channel1B_voltage[9])/10
        avg_2a = (channel2A_voltage[0]+channel2A_voltage[1]+channel2A_voltage[2]+channel2A_voltage[3]+channel2A_voltage[4]+channel2A_voltage[5]+channel2A_voltage[6]+channel2A_voltage[7]+channel2A_voltage[8]+channel2A_voltage[9])/10
        avg_2b = (channel2B_voltage[0]+channel2B_voltage[1]+channel2B_voltage[2]+channel2B_voltage[3]+channel2B_voltage[4]+channel2B_voltage[5]+channel2B_voltage[6]+channel2B_voltage[7]+channel2B_voltage[8]+channel2B_voltage[9])/10
        avg_3a = (channel3A_voltage[0]+channel3A_voltage[1]+channel3A_voltage[2]+channel3A_voltage[3]+channel3A_voltage[4]+channel3A_voltage[5]+channel3A_voltage[6]+channel3A_voltage[7]+channel3A_voltage[8]+channel3A_voltage[9])/10
        avg_3b = (channel3B_voltage[0]+channel3B_voltage[1]+channel3B_voltage[2]+channel3B_voltage[3]+channel3B_voltage[4]+channel3B_voltage[5]+channel3B_voltage[6]+channel3B_voltage[7]+channel3B_voltage[8]+channel3B_voltage[9])/10
        avg_4a = (channel4A_voltage[0]+channel4A_voltage[1]+channel4A_voltage[2]+channel4A_voltage[3]+channel4A_voltage[4]+channel4A_voltage[5]+channel4A_voltage[6]+channel4A_voltage[7]+channel4A_voltage[8]+channel4A_voltage[9])/10
        avg_4b = (channel4B_voltage[0]+channel4B_voltage[1]+channel4B_voltage[2]+channel4B_voltage[3]+channel4B_voltage[4]+channel4B_voltage[5]+channel4B_voltage[6]+channel4B_voltage[7]+channel4B_voltage[8]+channel4B_voltage[9])/10
        halfavg_1a = (channel1A_voltage[0]+channel1A_voltage[1]+channel1A_voltage[2]+channel1A_voltage[3]+channel1A_voltage[4])/5
        halfavg_1b = (channel1B_voltage[0]+channel1B_voltage[1]+channel1B_voltage[2]+channel1B_voltage[3]+channel1B_voltage[4])/5
        halfavg_2a = (channel2A_voltage[0]+channel2A_voltage[1]+channel2A_voltage[2]+channel2A_voltage[3]+channel2A_voltage[4])/5
        halfavg_2b = (channel2B_voltage[0]+channel2B_voltage[1]+channel2B_voltage[2]+channel2B_voltage[3]+channel2B_voltage[4])/5
        halfavg_3a = (channel3A_voltage[0]+channel3A_voltage[1]+channel3A_voltage[2]+channel3A_voltage[3]+channel3A_voltage[4])/5
        halfavg_3b = (channel3B_voltage[0]+channel3B_voltage[1]+channel3B_voltage[2]+channel3B_voltage[3]+channel3B_voltage[4])/5
        halfavg_4a = (channel4A_voltage[0]+channel4A_voltage[1]+channel4A_voltage[2]+channel4A_voltage[3]+channel4A_voltage[4])/5
        halfavg_4b = (channel4B_voltage[0]+channel4B_voltage[1]+channel4B_voltage[2]+channel4B_voltage[3]+channel4B_voltage[4])/5

        EPSstorageindex += 1
        if EPSstorageindex > 9:
            EPSstorageindex = 0
        

        ## Station Mode ##

        if stationmode == 1.0:
            self.mimic_screen.ids.stationmode_value.text = "Crew Rescue"
        elif stationmode == 2.0:
            self.mimic_screen.ids.stationmode_value.text = "Survival"
        elif stationmode == 3.0:
            self.mimic_screen.ids.stationmode_value.text = "Reboost"
        elif stationmode == 4.0:
            self.mimic_screen.ids.stationmode_value.text = "Proximity Operations"
        elif stationmode == 5.0:
            self.mimic_screen.ids.stationmode_value.text = "EVA"
        elif stationmode == 6.0:
            self.mimic_screen.ids.stationmode_value.text = "Microgravity"
        elif stationmode == 7.0:
            self.mimic_screen.ids.stationmode_value.text = "Standard"
        else:
            self.mimic_screen.ids.stationmode_value.text = "n/a"
            
        ##-------------------GNC Stuff---------------------------##    
        
        
        

        ##-------------------EPS Stuff---------------------------##

        if avg_total_voltage > 151.5:
            #for x in range(0,1000,1):
            #self.eps_screen.ids.eps_sun.color = 1,1,1,0.1
            #anim = Animation(self.eps_screen.ids.eps_sun.color=(1,1,1,1.0))
            #anim.start(self.eps_screen.ids.eps_sun.color)
            self.eps_screen.ids.eps_sun.color = 1,1,1,1
        else:
            #for x in range(1000,0,-1):
            #self.eps_screen.ids.eps_sun.color = 1,1,1,1.0
            #anim = Animation(self.eps_screen.ids.eps_sun.color=(1,1,1,0.1))
            #anim.start(self.eps_screen.ids.eps_sun.color)
            self.eps_screen.ids.eps_sun.color = 1,1,1,0.1

        if halfavg_1a < 151.5: #discharging
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_1a.color = 1,1,1,0.8
        elif avg_1a > 160.0: #charged
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_1a >= 151.5:  #charging
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_1a.color = 1,1,1,1.0
        if float(c1a) > 0.0:    #power channel offline!
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_1b < 151.5: #discharging
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_1b.color = 1,1,1,0.8
        elif avg_1b > 160.0: #charged
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_1b >= 151.5:  #charging
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_1b.color = 1,1,1,1.0
        if float(c1b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_2a < 151.5: #discharging
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_2a.color = 1,1,1,0.8
        elif avg_2a > 160.0: #charged
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_2a >= 151.5:  #charging
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_2a.color = 1,1,1,1.0
        if float(c2a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_2b < 151.5: #discharging
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_2b.color = 1,1,1,0.8
        elif avg_2b > 160.0: #charged
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_2b >= 151.5:  #charging
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_2b.color = 1,1,1,1.0
        if float(c2b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_3a < 151.5: #discharging
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3a.color = 1,1,1,0.8
        elif avg_3a > 160.0: #charged
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_3a >= 151.5:  #charging
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_3a.color = 1,1,1,1.0
        if float(c3a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_3b < 151.5: #discharging
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3b.color = 1,1,1,0.8
        elif avg_3b > 160.0: #charged
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_3b >= 151.5:  #charging
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_3b.color = 1,1,1,1.0
        if float(c3b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_4a < 151.5: #discharging
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_4a.color = 1,1,1,0.8
        elif avg_4a > 160.0: #charged
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_4a >= 151.5:  #charging
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_4a.color = 1,1,1,1.0
        if float(c4a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        if halfavg_4b < 151.5: #discharging
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_4b.color = 1,1,1,0.8
        elif avg_4b > 160.0: #charged
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif halfavg_4b >= 151.5:  #charging
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_4b.color = 1,1,1,1.0
        if float(c4b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        
        ##-------------------EVA Functionality-------------------##
        if stationmode == 5:
            evaflashevent = Clock.schedule_once(self.flashEVAbutton, 1)
    
        ##-------------------US EVA Functionality-------------------##
        
        airlock_pump_voltage = int((values[71])[0])
        airlock_pump_voltage_timestamp = float((timestamps[71])[0])
        airlock_pump_switch = int((values[72])[0])
        crewlockpres = float((values[16])[0])
        airlockpres = float((values[77])[0])

        if airlock_pump_voltage == 1:
            self.us_eva.ids.pumpvoltage.text = "Airlock Pump Power On!"
            self.us_eva.ids.pumpvoltage.color = 0.33,0.7,0.18
        else:
            self.us_eva.ids.pumpvoltage.text = "Airlock Pump Power Off"
            self.us_eva.ids.pumpvoltage.color = 0,0,0

        if airlock_pump_switch == 1:
            self.us_eva.ids.pumpswitch.text = "Airlock Pump Active!"
            self.us_eva.ids.pumpswitch.color = 0.33,0.7,0.18
        else:
            self.us_eva.ids.pumpswitch.text = "Airlock Pump Inactive"
            self.us_eva.ids.pumpswitch.color = 0,0,0
       
        ##activate EVA button flash
        if airlock_pump_voltage == 1 or crewlockpres < 734:
            usevaflashevent = Clock.schedule_once(self.flashUS_EVAbutton, 1)

        ##No EVA Currently
        if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres > 740 and airlockpres > 740: 
            eva = False   
            self.us_eva.ids.leak_timer.text = ""
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/BlankLights.png'
            self.us_eva.ids.EVA_occuring.color = 1,0,0
            self.us_eva.ids.EVA_occuring.text = "Currently No EVA"

        ##EVA Standby - NOT UNIQUE
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres > 740 and airlockpres > 740: 
            standby = True
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/StandbyLights.png'
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            self.us_eva.ids.EVA_occuring.text = "EVA Standby"
        else:
            standby = False

        ##EVA Prebreath Pressure
        if airlock_pump_voltage == 1 and crewlockpres > 740 and airlockpres > 740: 
            prebreath1 = True
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/PreBreatheLights.png'
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            self.us_eva.ids.EVA_occuring.text = "Pre-EVA Nitrogen Purge"
        
        ##EVA Depress1
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres < 740 and airlockpres > 740: 
            depress1 = True
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/DepressLights.png'

        ##EVA Leakcheck
        if airlock_pump_voltage == 1 and crewlockpres < 260 and crewlockpres > 250 and (depress1 or leakhold): 
            if depress1:
                holdstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
            leakhold = True
            depress1 = False
            self.us_eva.ids.EVA_occuring.text = "Leak Check in Progress!"
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            Clock.schedule_once(self.hold_timer, 1)
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/LeakCheckLights.png'
        else:
            leakhold = False

        ##EVA Depress2
        if airlock_pump_voltage == 1 and crewlockpres <= 250 and crewlockpres > 3 : 
            leakhold = False
            self.us_eva.ids.leak_timer.text = "Complete"
            self.us_eva.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/DepressLights.png'
        
        ##EVA in progress
        if crewlockpres < 2.5: 
            eva = True
            if obtained_EVA_crew == False:
                self.checkpasttweets()
            self.us_eva.ids.EVA_occuring.text = "EVA In Progress!!!"
            self.us_eva.ids.EVA_occuring.color = 0.33,0.7,0.18
            self.us_eva.ids.leak_timer.text = "Complete"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/InProgressLights.png'
            evatimerevent = Clock.schedule_once(self.EVA_clock, 1)

        ##Repress
        if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres >= 3 and crewlockpres < 734:
            eva = False
            self.us_eva.ids.EVA_occuring.color = 0,0,1
            self.us_eva.ids.EVA_occuring.text = "Crewlock Repressurizing"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/RepressLights.png'
        
        ##-------------------RS EVA Functionality-------------------##
        ##if eva station mode and not us eva
        if airlock_pump_voltage == 0 and crewlockpres >= 734:
            rsevaflashevent = Clock.schedule_once(self.flashRS_EVAbutton, 1)
    

        ##-------------------EVA Functionality End-------------------##

#        if (difference > -10) and (isinstance(App.get_running_app().root_window.children[0], Popup)==False):
#            LOSpopup = Popup(title='Loss of Signal', content=Label(text='Possible LOS Soon'),size_hint=(0.3,0.2),auto_dismiss=True)
#            LOSpopup.open()
#            print "popup"    

        iss_mass = "{:.2f}".format(float((values[48])[0]))
        position_x = "{:.2f}".format(float((values[55])[0]))
        position_y = "{:.2f}".format(float((values[56])[0]))
        position_z = "{:.2f}".format(float((values[57])[0]))
        velocity_x = "{:.2f}".format(float((values[58])[0]))
        velocity_y = "{:.2f}".format(float((values[59])[0]))
        velocity_z = "{:.2f}".format(float((values[60])[0]))
        
        altitude = "{:.2f}".format((math.sqrt( math.pow(float(position_x), 2) + math.pow(float(position_y), 2) + math.pow(float(position_z), 2) )-6371.00))
        velocity = "{:.2f}".format(((math.sqrt( math.pow(float(velocity_x), 2) + math.pow(float(velocity_y), 2) + math.pow(float(velocity_z), 2) ))/1.00))

        if (fakeorbitboolean == True and (mimicbutton == True or switchtofake == True)):
            if psarj2 <= 0.00:
                psarj2 = 360.0
            if ssarj2 >= 360.00:                
                ssarj2 = 0.0
            if beta1a2 >= 360.00:
                beta1a2 = 0.0
            if beta1b2 >= 360.00:
                beta1b2 = 0.0
            if beta2a2 >= 360.00:
                beta2a2 = 0.0
            if beta2b2 <= 0.00:
                beta2b2 = 360.0
            if beta3a2 >= 360.00:
                beta3a2 = 0.0
            if beta3b2 >= 360.00:
                beta3b2 = 0.0
            if beta4a2 <= 0.00:
                beta4a2 = 360.0
            if beta4b2 >= 360.00:
                beta4b2 = 0.0
            self.fakeorbit_screen.ids.fakepsarj_value.text = "{:.2f}".format(psarj2)
            self.fakeorbit_screen.ids.fakessarj_value.text = "{:.2f}".format(ssarj2)
            
            #psarj2 -= 0.0666
            psarj2 -= 6.66
            #ssarj2 += 0.0666
            ssarj2 += 6.66

            beta1a2 += 3.00
            beta1b2 += 3.00
            beta2a2 += 3.00
            beta2b2 -= 3.00
            beta3a2 += 3.00
            beta3b2 += 3.00
            beta4a2 -= 3.00
            beta4b2 += 3.00

            self.serialWrite("PSARJ=" + str(psarj2) + " ")
            self.serialWrite("SSARJ=" + str(ssarj2) + " ")
            self.serialWrite("PTRRJ=" + str(ptrrj) + " ")
            self.serialWrite("STRRJ=" + str(strrj) + " ")
            self.serialWrite("Beta1B=" + str(beta1b2) + " ")
            self.serialWrite("Beta1A=" + str(beta1a2) + " ")
            self.serialWrite("Beta2B=" + str(beta2b2) + " ")
            self.serialWrite("Beta2A=" + str(beta2a2) + " ")
            self.serialWrite("Beta3B=" + str(beta3b2) + " ")
            self.serialWrite("Beta3A=" + str(beta3a2) + " ")
            self.serialWrite("Beta4B=" + str(beta4b2) + " ")
            self.serialWrite("Beta4A=" + str(beta4a2) + " ")
            self.serialWrite("AOS=" + str(aos) + " ")
            self.serialWrite("Voltage1A=" + str(v1a) + " ")
            self.serialWrite("Voltage2A=" + str(v2a) + " ")
            self.serialWrite("Voltage3A=" + str(v3a) + " ")
            self.serialWrite("Voltage4A=" + str(v4a) + " ")
            self.serialWrite("Voltage1B=" + str(v1b) + " ")
            self.serialWrite("Voltage2B=" + str(v2b) + " ")
            self.serialWrite("Voltage3B=" + str(v3b) + " ")
            self.serialWrite("Voltage4B=" + str(v4b) + " ")
       
        self.eps_screen.ids.psarj_value.text = psarj + "deg" 
        self.eps_screen.ids.ssarj_value.text = ssarj + "deg"
        self.tcs_screen.ids.ptrrj_value.text = ptrrj + "deg"
        self.tcs_screen.ids.strrj_value.text = strrj + "deg"
        self.eps_screen.ids.beta1b_value.text = beta1b
        self.eps_screen.ids.beta1a_value.text = beta1a
        self.eps_screen.ids.beta2b_value.text = beta2b
        self.eps_screen.ids.beta2a_value.text = beta2a
        self.eps_screen.ids.beta3b_value.text = beta3b
        self.eps_screen.ids.beta3a_value.text = beta3a
        self.eps_screen.ids.beta4b_value.text = beta4b
        self.eps_screen.ids.beta4a_value.text = beta4a
        self.eps_screen.ids.c1a_value.text = c1a + "A"
        self.eps_screen.ids.v1a_value.text = v1a + "V"
        self.eps_screen.ids.c1b_value.text = c1b + "A"
        self.eps_screen.ids.v1b_value.text = v1b + "V"
        self.eps_screen.ids.c2a_value.text = c2a + "A"
        self.eps_screen.ids.v2a_value.text = v2a + "V"
        self.eps_screen.ids.c2b_value.text = c2b + "A"
        self.eps_screen.ids.v2b_value.text = v2b + "V"
        self.eps_screen.ids.c3a_value.text = c3a + "A"
        self.eps_screen.ids.v3a_value.text = v3a + "V"
        self.eps_screen.ids.c3b_value.text = c3b + "A"
        self.eps_screen.ids.v3b_value.text = v3b + "V"
        self.eps_screen.ids.c4a_value.text = c4a + "A"
        self.eps_screen.ids.v4a_value.text = v4a + "V"
        self.eps_screen.ids.c4b_value.text = c4b + "A"
        self.eps_screen.ids.v4b_value.text = v4b + "V"
        self.mimic_screen.ids.altitude_value.text = str(altitude) + " km"
        self.mimic_screen.ids.velocity_value.text = str(velocity) + " m/s"
        self.mimic_screen.ids.stationmass_value.text = str(iss_mass) + " kg"

        self.us_eva.ids.EVA_needle.angle = float(self.map_rotation(0.0193368*float(crewlockpres)))
        self.us_eva.ids.crewlockpressure_value.text = "{:.2f}".format(0.0193368*float(crewlockpres))
       
        psi_bar_x = self.map_psi_bar(0.0193368*float(crewlockpres)) #convert to torr
        
        self.us_eva.ids.EVA_psi_bar.pos_hint = {"center_x": psi_bar_x, "center_y": 0.56} 
       
        if float(aos) == 1.00:
            #self.changeColors(0,1,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = False
               if mimicbutton == True:
                   switchtofake = False
            if LS_Subscription == True:
                self.signal_acquired()
            else:
                self.signal_unsubscribed()
        elif float(aos) == 0.00:
            #self.changeColors(1,0,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.signal_lost()
        elif float(aos) == 2.00:
            #self.changeColors(1,0.5,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.signal_stale()

        if (mimicbutton == True and float(aos) == 1.00): 
            self.serialWrite("PSARJ=" + psarj + " ")
            self.serialWrite("SSARJ=" + ssarj + " ")
            self.serialWrite("PTRRJ=" + ptrrj + " ")
            self.serialWrite("STRRJ=" + strrj + " ")
            self.serialWrite("Beta1B=" + beta1b + " ")
            self.serialWrite("Beta1A=" + beta1a + " ")
            self.serialWrite("Beta2B=" + beta2b + " ")
            self.serialWrite("Beta2A=" + beta2a + " ")
            self.serialWrite("Beta3B=" + beta3b + " ")
            self.serialWrite("Beta3A=" + beta3a + " ")
            self.serialWrite("Beta4B=" + beta4b + " ")
            self.serialWrite("Beta4A=" + beta4a + " ")
            self.serialWrite("AOS=" + aos + " ")
            self.serialWrite("Voltage1A=" + v1a + " ")
            self.serialWrite("Voltage2A=" + v2a + " ")
            self.serialWrite("Voltage3A=" + v3a + " ")
            self.serialWrite("Voltage4A=" + v4a + " ")
            self.serialWrite("Voltage1B=" + v1b + " ")
            self.serialWrite("Voltage2B=" + v2b + " ")
            self.serialWrite("Voltage3B=" + v3b + " ")
            self.serialWrite("Voltage4B=" + v4b + " ")

#All GUI Screens are on separate kv files
Builder.load_file('/home/pi/Mimic/Pi/Screens/Settings_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/FakeOrbitScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Orbit_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EPS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/GNC_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/TCS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_US_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_RS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_Main_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_Pictures.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Crew_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/RS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/ManualControlScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/MimicScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CalibrateScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/MainScreen.kv')

Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
ScreenManager:
    Settings_Screen:
    FakeOrbitScreen:
    Orbit_Screen:
    EPS_Screen:
    CT_Screen:
    GNC_Screen:
    TCS_Screen:
    EVA_US_Screen:
    EVA_RS_Screen:
    EVA_Main_Screen:
    EVA_Pictures:
    RS_Screen:
    Crew_Screen:
    ManualControlScreen:
    MimicScreen:
    CalibrateScreen:
    MainScreen:
''')

if __name__ == '__main__':
    MainApp().run()
