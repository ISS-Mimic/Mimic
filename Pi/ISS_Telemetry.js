function alert(message)
{

}

var ls = require("lightstreamer-client");
var sqlite3 = require("sqlite3");

//var db = new sqlite3.Database("./iss_telemetry.db", sqlite3.OPEN_READWRITE, db_err);
var db = new sqlite3.Database("/dev/shm/iss_telemetry.db", sqlite3.OPEN_CREATE | sqlite3.OPEN_READWRITE);
db.serialize(function() {
db.run("CREATE TABLE IF NOT EXISTS telemetry (`Label` TEXT PRIMARY KEY, `Timestamp` TEXT, `Value` TEXT, `ID` TEXT, `dbID` NUMERIC )");
db.run("INSERT OR IGNORE INTO telemetry VALUES('psarj','1216.72738833328','233.039337158203','S0000004',1)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('ssarj','1216.72738833328','126.911819458008','S0000003',2)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('ptrrj','1175.8188055555','-39.9920654296875','S0000002',3)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('strrj','1216.72741666661','25.1238956451416','S0000001',4)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta1b','1216.72669444442','253.663330078125','S6000008',5)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta1a','1216.72669444442','110.802612304688','S4000007',6)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta2b','1216.72724999997','291.62109375','P6000008',7)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta2a','1216.72344388889','345.602416992188','P4000007',8)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta3b','1216.72355444445','194.144897460938','S6000007',9)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta3a','1216.72669444442','249.076538085938','S4000008',10)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta4b','1216.72669444442','69.818115234375','P6000007',11)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('beta4a','1216.7269722222','14.3975830078125','P4000008',12)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('aos','1216.72733833333','1','AOS',13)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('los','7084.92338888884','0','LOS',14)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa1_elevation','1216.7273047222','101.887496948242','S1000005',15)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sgant_elevation','1216.72727777772','105.172134399414','Z1000014',16)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('crewlock_pres','1216.65458361109','754.457946777344','AIRLOCK000049',17)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sgant_xel','1216.72727777772','-38.6938552856445','Z1000015',18)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa1_azimuth','1216.71619333333','185.268753051758','S1000004',19)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopb_flowrate','1216.69486111111','4349.26708984375','P1000001',20)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopb_pressure','1216.72730527778','2162.86865234375','P1000002',21)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopb_temp','1216.72108277778','4.13970804214478','P1000003',22)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopa_flowrate','1216.72683361106','3519.21850585938','S1000001',23)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopa_pressure','1216.70883222222','2103.71728515625','S1000002',24)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('loopa_temp','1216.72386055556','3.63912987709045','S1000003',25)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_1a','1216.72469388889','160.576171875','S4000001',26)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_1b','1216.72480444445','159.49951171875','S6000004',27)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_2a','1216.72422194441','159.90966796875','P4000001',28)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_2b','1216.72433249997','152.73193359375','P6000004',29)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_3a','1216.72469388889','158.78173828125','S4000004',30)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_3b','1216.72480444445','160.986328125','S6000001',31)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_4a','1216.72422194441','158.73046875','P4000004',32)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('voltage_4b','1216.71599916663','159.8583984375','P6000001',33)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_1a','1216.72597222222','-32.1090566730273','S4000002',34)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_1b','1216.72597222222','-65.9772260650065','S6000005',35)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_2a','1216.72574972219','-45.60829685216','P4000002',36)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_2b','1216.72594388889','-30.1572487651965','P6000005',37)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_3a','1216.72597222222','-41.1726404259626','S4000005',38)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_3b','1216.72597222222','-35.8874645656566','S6000002',39)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_4a','1216.72594388889','-44.8238382407841','P4000005',40)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('current_4b','1216.72594388889','-35.2639276439644','P6000002',41)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('kuband_transmit','1216.7250719444','1','Z1000013',42)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('ptrrj_mode','1161.24824999995','4','S0000006',43)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('strrj_mode','1161.24824999995','4','S0000007',44)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('psarj_mode','1160.65219388889','5','S0000008',45)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('ssarj_mode','1160.65219388889','5','S0000009',46)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('russian_mode','1160.65213861108','7','RUSSEG000001',47)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('iss_mode','1160.65419361108','1','USLAB000086',48)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('iss_mass','1161.24836194442','417501.5625','USLAB000039',49)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('us_gnc_mode','1160.65438777778','5','USLAB000012',50)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa2_elevation','1216.7273047222','101.90625','P1000005',51)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa2_azimuth','1216.71572138886','185.268753051758','P1000004',52)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa2_status','1160.66299888889','1','P1000007',53)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('sasa1_status','1160.66066611111','1','S1000009',54)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('active_sasa','1160.66272111111','1','USLAB000092',55)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('position_x','1216.725805','29.8297033276271','USLAB000032',56)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('position_y','1216.725805','5964.89191167363','USLAB000033',57)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('position_z','1216.725805','-3237.06743854422','USLAB000034',58)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('velocity_x','1216.725805','-5433.68688146446','USLAB000035',59)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('velocity_y','1216.725805','-2551.23487465513','USLAB000036',60)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('velocity_z','1216.725805','-4762.70709805804','USLAB000037',61)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU1_VOLTS','1216.69152805554','-0.0286679994314909','AIRLOCK000001',62)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU1_AMPS','1216.69041694442','-0.00489299977198243','AIRLOCK000002',63)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU2_VOLTS','1216.68263916665','-0.0286679994314909','AIRLOCK000003',64)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_EMU2_AMPS','1216.69013916665','-0.00489299977198243','AIRLOCK000004',65)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_IRU_Utility_VOLTS','1216.68238833328','-0.0286679994314909','AIRLOCK000005',66)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('PSA_IRU_Utility_AMPS','1216.7271105555','-0.00489299977198243','AIRLOCK000006',67)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_1_VOLTS','1216.69177749998','-0.0286679994314909','AIRLOCK000007',68)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_1_AMPS','1216.6839997222','-0.00489299977198243','AIRLOCK000008',69)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_2_VOLTS','1216.72705527776','-0.0286679994314909','AIRLOCK000009',70)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('UIA_EV_2_AMPS','1216.69122194442','-0.00489299977198243','AIRLOCK000010',71)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_AL1A4A_A_RPC_01_Depress_Pump_On_Off_Stat','1160.66247166667','0','AIRLOCK000047',72)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_Depress_Pump_Power_Switch','1161.24977777772','0','AIRLOCK000048',73)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Hi_P_Supply_Vlv_Actual_Posn','1161.24997194442','0','AIRLOCK000050',74)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Lo_P_Supply_Vlv_Actual_Posn','1161.24997194442','1','AIRLOCK000051',75)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_N2_Supply_Vlv_Actual_Posn','1161.24997194442','1','AIRLOCK000052',76)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_CCAA_State','1161.24994361109','5','AIRLOCK000053',77)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_PCA_Cabin_Pressure','1216.07402833336','752.088439941406','AIRLOCK000054',78)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Hi_P_Supply_Pressure','1216.72674916665','12801.83984375','AIRLOCK000055',79)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_O2_Lo_P_Supply_Pressure','1216.72388888889','5624.67041015625','AIRLOCK000056',80)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Airlock_N2_Supply_Pressure','1216.66397138887','11619.3896484375','AIRLOCK000057',81)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node2_MTL_PPA_Avg_Accum_Qty','1161.2497227778','42.8092460632324','NODE2000001',82)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node2_LTL_PPA_Avg_Accum_Qty','1216.72069444444','33.9924049377441','NODE2000002',83)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_2_CCAA_State','1161.24991694444','5','NODE2000003',84)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node2_LTL_TWMV_Out_Temp','1216.72733333336','10.0628938674927','NODE2000006',85)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node2_MTL_TWMV_Out_Temp','1216.694555','17.1698589324951','NODE2000007',86)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppO2','1215.93880527774','171.485071057186','NODE3000001',87)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppN2','1215.93880527774','566.382082394791','NODE3000002',88)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_MCA_ppCO2','1215.93880527774','3.21665350504667','NODE3000003',89)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_UPA_Current_State','1214.98497222225','32','NODE3000004',90)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_UPA_WSTA_Qty_Ctrl_Pct','1216.18163861109','48','NODE3000005',91)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Process_Cmd_Status','1209.33855500003','4','NODE3000006',92)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Process_Step','1209.58580666668','4','NODE3000007',93)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Waste_Water_Qty_Ctrl','1216.72741805553','13.1700000762939','NODE3000008',94)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_WPA_Water_Storage_Qty_Ctrl','1216.72741805553','82.1500015258789','NODE3000009',95)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_OGA_Process_Cmd_Status','1160.66252694441','1','NODE3000010',96)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_OGA_O2_Production_Rate','1216.72730500003','2.7396981716156','NODE3000011',97)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node3_MTL_TWMV_Out_Temp','1216.69444444444','17.1069641113281','NODE3000012',98)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node3_LTL_TWMV_Out_Temp','1216.59625083334','9.4375','NODE3000013',99)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node3_MTL_PPA_Avg_Accum_Qty','1214.82188833336','78.7650146484375','NODE3000017',100)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node_3_CCAA_State','1161.2465836111','5','NODE3000018',101)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Node3_LTL_PPA_Avg_Accum_Qty','1214.23022166669','59.9398651123047','NODE3000019',102)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_2A_PVCU_On_Off_V_Stat','1161.24858444446','1','P4000003',103)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4A_PVCU_On_Off_V_Stat','1161.24980611112','1','P4000006',104)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4B_RBI_6_Integ_I','0','0','P6000002',105)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_4B_PVCU_On_Off_V_Stat','1161.25161166668','1','P6000003',106)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_2B_PVCU_On_Off_V_Stat','1161.24980611112','1','P6000006',107)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS1_On','1161.24980527778','0','RUSSEG000002',108)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS2_On','1161.24980527778','0','RUSSEG000003',109)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_ECW_KURS_Fail','1161.24980527778','0','RUSSEG000004',110)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS_Rng','1161.24991749995','96348.265625','RUSSEG000005',111)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_KURS_Vel','1161.24991749995','134.808670043945','RUSSEG000006',112)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Test_Mode_RS','1161.24980527778','0','RUSSEG000007',113)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Capture_Signal_RS','1161.24980527778','0','RUSSEG000008',114)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Target_Acquisition_Signal_RS','1161.24980527778','0','RUSSEG000009',115)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_Functional_Mode_Signal_RS','1161.24980527778','0','RUSSEG000010',116)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SM_KURS_P_In_Stand_by_Mode_RS','1161.24980527778','0','RUSSEG000011',117)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Dock_Contact','1161.24977833331','0','RUSSEG000012',118)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Forward_Port_Engaged','1161.24977833331','1','RUSSEG000013',119)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Aft_Port_Engaged','1161.24977833331','1','RUSSEG000014',120)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000015',121)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_FGB_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000016',122)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_UDM_Nadir_Port_Engaged','1161.24977833331','1','RUSSEG000017',123)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_MRM1_Port_Engaged','1161.24977833331','1','RUSSEG000018',124)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_MRM2_Port_Engaged','1161.24977833331','1','RUSSEG000019',125)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_ETOV_Hooks_Closed','1161.24986222221','0','RUSSEG000020',126)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Act_Att_Ref_Frame','1161.24977833331','1','RUSSEG000021',127)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_RS_Is_Master','1161.24977833331','0','RUSSEG000022',128)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_Ready_For_Indicator','1161.24977833331','0','RUSSEG000023',129)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSProp_SM_Thrstr_Mode_Terminated','1161.24983388888','0','RUSSEG000024',130)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RSMCS_SM_SUDN_Mode','1160.65194444444','6','RUSSEG000025',131)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('SARJ_Port_Commanded_Position','1216.72741666661','233.195175170898','S0000005',132)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S01A_C_RPC_01_Ext_1_MDM_On_Off_Stat','1160.6606108333','1','S0000010',133)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S01A_C_RPC_16_S0_1_MDM_On_Off_Stat','1160.66217666666','1','S0000011',134)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S02B_C_RPC_01_Ext_2_MDM_On_Off_Stat','1160.6606108333','0','S0000012',135)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S02B_C_RPC_16_S0_2_MDM_On_Off_Stat','1160.6606108333','1','S0000013',136)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S11A_C_RPC_03_STR_MDM_On_Off_Stat','1160.66066611111','1','S1000006',137)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S11A_C_RPC_16_S1_1_MDM_On_Off_Stat','1160.66066611111','1','S1000007',138)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_S12B_B_RPC_05_S1_2_MDM_On_Off_Stat','1160.66069444444','1','S1000008',139)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_1A_PVCU_On_Off_V_Stat','1161.2484738889','1','S4000003',140)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_3A_PVCU_On_Off_V_Stat','1161.24980611112','1','S4000006',141)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_3B_PVCU_On_Off_V_Stat','1161.2484738889','1','S6000003',142)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('DCSU_1B_PVCU_On_Off_V_Stat','1161.24980611112','1','S6000006',143)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Time of Occurrence','1216.72744333333','4380218418','TIME_000001',144)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Year of Occurrence','1160.65017138885','2018','TIME_000002',145)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG1_Online','1161.24816638887','1','USLAB000001',146)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG2_Online','1161.24816638887','1','USLAB000002',147)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG3_Online','1161.24816638887','1','USLAB000003',148)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SEQ_CMG4_Online','1161.24816638887','1','USLAB000004',149)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Num_CMGs_Online','1161.24808277773','4','USLAB000005',150)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_X','1216.72744388892','-2.45458972872734','USLAB000006',151)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_Y','1216.72744388892','4.61879036814499','USLAB000007',152)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Unlim_Cntl_Trq_InBody_Z','1216.72744388892','-2.27159083915615','USLAB000008',153)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Mag','1216.72736222221','2185.16832879028','USLAB000009',154)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Cap_Pct','1216.72736222221','11.193434715271','USLAB000010',155)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Desat_Request_Inh','1161.25058416665','0','USLAB000011',156)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_AD_Selected_Att_Source','1161.24819611112','1','USLAB000013',157)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_AD_Selected_Rate_Source','1161.24819611112','1','USLAB000014',158)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SD_Selected_State_Source','1161.24850083331','4','USLAB000015',159)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_Att_Cntl_Type','1161.24808277773','1','USLAB000016',160)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_Att_Cntl_Ref_Frame','1160.65273222221','0','USLAB000017',161)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_0','1216.72744416667','0.999212622642517','USLAB000018',162)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_1','1216.72744416667','0.00867813266813755','USLAB000019',163)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_2','1216.72744416667','-0.0168247651308775','USLAB000020',164)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_LVLH_Att_Quatrn_3','1216.72744416667','-0.0348674207925797','USLAB000021',165)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_X','1216.72741777778','0.368115151294135','USLAB000022',166)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_Y','1216.72741777778','0.0822624275713228','USLAB000023',167)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Att_Error_Z','1216.72741777778','-0.00235306124983981','USLAB000024',168)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_X','1216.72744416667','0.00437836543317244','USLAB000025',169)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_Y','1216.72744416667','-0.0643700269413879','USLAB000026',170)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Pointing_Current_Inert_Rate_Vector_Z','1216.72744416667','0.00107732213344025','USLAB000027',171)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_0_Cmd','1160.65173305551','0.999223709106445','USLAB000028',172)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_1_Cmd','1160.65173305551','0.00549489445984364','USLAB000029',173)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_2_Cmd','1160.65173305551','-0.0176546052098274','USLAB000030',174)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Act_CCDB_AttQuatrn_3_Cmd','1160.65173305551','-0.0347869843244553','USLAB000031',175)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_CMG_Mom_Act_Cap','1216.72466555556','19521.8739049785','USLAB000038',176)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_PS_Solar_Beta_Angle','1216.72409416662','-62.734375','USLAB000040',177)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_Loss_Of_CMG_Att_Cntl_Latched_Caution','1161.2498047222','0','USLAB000041',178)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CCS_Loss_of_ISS_Attitude_Control_Warning','1161.24986250003','0','USLAB000042',179)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_GPS1_Operational_Status','1216.72222222222','0','USLAB000043',180)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_GPS2_Operational_Status','1216.32369361109','0','USLAB000044',181)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinBrg_Temp1','1216.72562749995','27.6041679382324','USLAB000045',182)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinBrg_Temp1','1216.72573805551','22.6085071563721','USLAB000046',183)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinBrg_Temp1','1216.72237777776','34.7960090637207','USLAB000047',184)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinBrg_Temp1','1216.72579333332','34.8828163146973','USLAB000048',185)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinBrg_Temp2','1216.7223211111','26.1024322509766','USLAB000049',186)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinBrg_Temp2','1216.72573805551','17.3784732818604','USLAB000050',187)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinBrg_Temp2','1216.52016749998','45.776912689209','USLAB000051',188)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinBrg_Temp2','1216.72579333332','33.589412689209','USLAB000052',189)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppO2','1161.24661055558','156.316830573616','USLAB000053',190)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppN2','1161.24661055558','574.227483380585','USLAB000054',191)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_MCA_ppCO2','1160.65574972219','2.2482170546557','USLAB000055',192)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_LTL_PPA_Avg_Accum_Qty','1215.30244388892','79.7446594238281','USLAB000056',193)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_MTL_PPA_Avg_Accum_Qty','1191.26744388892','80.2742004394531','USLAB000057',194)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_PCA_Cabin_Pressure','1216.52375055558','751.785461425781','USLAB000058',195)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB1P6_CCAA_In_T1','1216.71502694441','23.3861961364746','USLAB000059',196)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_MTL_Regen_TWMV_Out_Temp','1216.68211083333','17.2327518463135','USLAB000060',197)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_LTL_TWMV_Out_Temp','1216.70669361108','9.0625','USLAB000061',198)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_VRS_Vent_Vlv_Posn_Raw','1185.75786055558','1','USLAB000062',199)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB_VES_Vent_Vlv_Posn_Raw','1185.70063833336','1','USLAB000063',200)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB1P6_CCAA_State','1161.2465836111','5','USLAB000064',201)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('LAB1S6_CCAA_State','1161.2465836111','4','USLAB000065',202)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_07_CC_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000066',203)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_03_CC_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000067',204)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1A4A_E_RPC_01_CC_3_MDM_On_Off_Stat','1160.66283305552','1','USLAB000068',205)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_09_Int_1_MDM_On_Off_Stat','1160.66283305552','0','USLAB000069',206)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_04_Int_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000070',207)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_11_PL_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000071',208)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD22B_A_RPC_01_PL_2_MDM_On_Off_Stat','1160.66283305552','1','USLAB000072',209)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_B_RPC_14_GNC_1_MDM_On_Off_Stat','1160.65444444444','1','USLAB000073',210)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_03_GNC_2_MDM_On_Off_Stat','1160.65447138886','1','USLAB000074',211)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD11B_A_RPC_08_PMCU_1_MDM_On_Off_Stat','1160.66283305552','1','USLAB000075',212)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_01_PMCU_2_MDM_On_Off_Stat','1160.66283305552','0','USLAB000076',213)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_B_RPC_09_LAB_1_MDM_On_Off_Stat','1160.66277777778','1','USLAB000077',214)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_04_LAB_2_MDM_On_Off_Stat','1160.66280472219','1','USLAB000078',215)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA2B_E_RPC_13_LAB_3_MDM_On_Off_Stat','1160.66280472219','1','USLAB000079',216)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_D_RPC_01_LAB_FSEGF_Sys_Pwr_1_On_Off_Stat','1160.66280472219','0','USLAB000080',217)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CA_AttMnvr_In_Progress','1160.65958333333','0','USLAB000081',218)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_Std_Cmd_Accept_Cnt','1216.693305','4089','USLAB000082',219)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_Data_Load_Cmd_Accept_Cnt','1216.05608333336','28711','USLAB000083',220)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Coarse_Time','1216.72722222222','1203093836','USLAB000084',221)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Fine_Time','1216.72747166667','0.59765625','USLAB000085',222)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Prim_CCS_MDM_PCS_Cnct_Cnt','1171.44763999999','7','USLAB000087',223)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_1_Activity_Indicator','1161.24988833328','1','USLAB000088',224)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_2_Activity_Indicator','1161.24988833328','1','USLAB000089',225)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_3_Activity_Indicator','1161.24988833328','1','USLAB000090',226)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Ku_HRFM_VBSP_4_Activity_Indicator','1161.24988833328','1','USLAB000091',227)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Audio_IAC1_Mode_Indication','1161.24972305556','1','USLAB000093',228)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Audio_IAC2_Mode_Indication','1161.24972333332','1','USLAB000094',229)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_9_Source_ID','1166.30116777778','19','USLAB000095',230)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_13_Source_ID','1161.24977888889','28','USLAB000096',231)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_14_Source_ID','1161.24977888889','19','USLAB000097',232)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('VDS_Destination_29_Source_ID','1161.24977888889','0','USLAB000098',233)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LAD52B_A_RPC_08_UHF_SSSR_1_On_Off_Stat','1160.66283305552','0','USLAB000099',234)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('RPCM_LA1B_H_RPC_04_UHF_SSSR_2_On_Off_Stat','1170.84539000001','0','USLAB000100',235)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('UHF_Frame_Sync','1170.83724944439','0','USLAB000101',236)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_SD_Selected_State_Time_Tag','1216.725805','1203093820.00567','USLAB000102',237)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_IG_Vibration','1216.68952833335','0','Z1000001',238)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_IG_Vibration','1216.68958500001','0.006805419921875','Z1000002',239)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_IG_Vibration','1216.68961194442','0.005828857421875','Z1000003',240)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_IG_Vibration','1216.68688944446','0.004364013671875','Z1000004',241)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_SpinMtr_Current','1216.6867788889','0.63671875','Z1000005',242)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_SpinMtr_Current','1216.68961194442','0.5029296875','Z1000006',243)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_SpinMtr_Current','1216.68964027776','1.0947265625','Z1000007',244)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_SpinMtr_Current','1216.68691777779','0.9013671875','Z1000008',245)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG1_Current_Wheel_Speed','1216.7223211111','6601','Z1000009',246)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG2_Current_Wheel_Speed','1216.72573805551','6601','Z1000010',247)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG3_Current_Wheel_Speed','1216.7273886111','6601','Z1000011',248)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('USGNC_CMG4_Current_Wheel_Speed','1216.72579333332','6600','Z1000012',249)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('eva_crew_1','0','crew1','0',250)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('eva_crew_2','0','crew2','0',251)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('us_eva_#','0','43','0',252)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('rs_eva_#','0','43','0',253)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('last_us_eva_duration','0','450','0',254)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('last_rs_eva_duration','0','450','0',255)");
db.run("INSERT OR IGNORE INTO telemetry VALUES('Lightstreamer','0','Subscribed','0',0)");
});

var telemetry = require("./Telemetry_identifiers.js");
var classes = ["TimeStamp", "Value"];

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com", "ISSLIVE");

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE", telemetry.identifiers, classes);
var timeSub = new ls.Subscription("MERGE", "TIME_000001", ["TimeStamp", "Value", "Status.Class", "Status.Indicator"]);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

var AOS;
var AOSnum = 0;
var now = new Date();
var gmtoff = (now.getTimezoneOffset())/60;
var start = new Date(now.getFullYear(), 0, 0);
var diff = (now - start) + ((start.getTimezoneOffset() - now.getTimezoneOffset()) * 60 * 1000);
var oneDay = 1000 * 60 * 60 * 24;
var timestampnow = (diff / oneDay) * 24 + gmtoff;


console.log('ISS Telemetry script active');
//console.log('Current timestamp: ' + timestampnow);

lsClient.connect();

sub.addListener({
  onSubscription: function() {
    console.log("Subscribed");
    db.run("UPDATE telemetry set Value = ? where Label = ?", "Subscribed", "Lightstreamer");
  },
  onUnsubscription: function() {
    console.log("Unsubscribed");
    db.run("UPDATE telemetry set Value = ? where Label = ?", "Unsubscribed", "Lightstreamer");
  },
  onItemUpdate: function(update) 
  {
    switch (update.getItemName())
    {
        case "USLAB000092":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "active_sasa");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "active_sasa");
            break;
        case "S0000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "psarj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "psarj");
            break;
        case "S0000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ssarj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ssarj");
            break;
        case "S0000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ptrrj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ptrrj");
            break;
        case "S0000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "strrj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "strrj");
            break;
        case "S6000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1b");
            break;
        case "S6000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3b");
            break;
        case "S4000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3a");
            break;
        case "S4000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1a");
            break;
        case "P4000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2a");
            break;
        case "P4000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4a");
            break;
        case "P6000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4b");
            break;
        case "P6000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2b");
            break;
        case "Z1000014":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sgant_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sgant_elevation");
            break;
        case "S1000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_elevation");
            break;
        case "AIRLOCK000049":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "crewlock_pres");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "crewlock_pres");
            break;
        case "S4000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_1a");
            break;
        case "S4000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_1a");
            break;
        case "S6000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_1b");
            break;
        case "S6000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_1b");
            break;
        case "P4000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_2a");
            break;
        case "P4000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_2a");
            break;
        case "P6000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_2b");
            break;
        case "P6000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_2b");
            break;
        case "S4000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_3a");
            break;
        case "S4000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_3a");
            break;
        case "S6000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_3b");
            break;
        case "S6000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_3b");
            break;
        case "P4000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_4a");
            break;
        case "P4000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_4a");
            break;
        case "P6000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_4b");
            break;
        case "P6000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_4b");
            break;
        case "S0000006":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ptrrj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ptrrj_mode");
            break;
        case "S0000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "strrj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "strrj_mode");
            break;
        case "S0000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "psarj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "psarj_mode");
            break;
        case "S0000009":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ssarj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ssarj_mode");
            break;
        case "Z1000013":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "kuband_transmit");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "kuband_transmit");
            break;
        case "RUSSEG000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "russian_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "russian_mode");
            break;
        case "USLAB000039":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "iss_mass");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "iss_mass");
            break;
        case "USLAB000012":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "us_gnc_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "us_gnc_mode");
            break;
        case "USLAB000086":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "iss_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "iss_mode");
            break;
        case "S1000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_flowrate");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_flowrate");
            break;
        case "S1000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_pressure");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_pressure");
            break;
        case "S1000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_temp");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_temp");
            break;
        case "P1000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_flowrate");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_flowrate");
            break;
        case "P1000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_pressure");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_pressure");
            break;
        case "P1000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_temp");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_temp");
            break;
        case "Z1000015":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sgant_xel");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sgant_xel");
            break;
        case "P1000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_azimuth");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_azimuth");
            break;
        case "P1000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_elevation");
            break;
        case "P1000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_status");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_status");
            break;
        case "S1000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_azimuth");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_azimuth");
            break;
        case "S1000009":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_status");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_status");
            break;
        case "USLAB000032":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_x");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_x");
            break;
        case "USLAB000033":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_y");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_y");
            break;
        case "USLAB000034":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_z");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_z");
            break;
        case "USLAB000035":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_x");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_x");
            break;
        case "USLAB000036":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_y");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_y");
            break;
        case "USLAB000037":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_z");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_z");
            break;
        case "AIRLOCK000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000001");
            break;
        case "AIRLOCK000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000002");
            break;
        case "AIRLOCK000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000003");
            break;
        case "AIRLOCK000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000004");
            break;
        case "AIRLOCK000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000005");
            break;
        case "AIRLOCK000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000006");
            break;
        case "AIRLOCK000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000007");
            break;
        case "AIRLOCK000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000008");
            break;
        case "AIRLOCK000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000009");
            break;
        case "AIRLOCK000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000010");
            break;
        case "AIRLOCK000047":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000047");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000047");
            break;
        case "AIRLOCK000048":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000048");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000048");
            break;
        case "AIRLOCK000050":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000050");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000050");
            break;
        case "AIRLOCK000051":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000051");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000051");
            break;
        case "AIRLOCK000052":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000052");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000052");
            break;
        case "AIRLOCK000053":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000053");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000053");
            break;
        case "AIRLOCK000054":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000054");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000054");
            break;
        case "AIRLOCK000055":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000055");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000055");
            break;
        case "AIRLOCK000056":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000056");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000056");
            break;
        case "AIRLOCK000057":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000057");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000057");
            break;
        case "NODE2000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000001");
            break;
        case "NODE2000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000002");
            break;
        case "NODE2000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000003");
            break;
        case "NODE2000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000006");
            break;
        case "NODE2000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000007");
            break;
        case "NODE3000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000001");
            break;
        case "NODE3000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000002");
            break;
        case "NODE3000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000003");
            break;
        case "NODE3000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000004");
            break;
        case "NODE3000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000005");
            break;
        case "NODE3000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000006");
            break;
        case "NODE3000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000007");
            break;
        case "NODE3000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000008");
            break;
        case "NODE3000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000009");
            break;
        case "NODE3000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000010");
            break;
        case "NODE3000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000011");
            break;
        case "NODE3000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000012");
            break;
        case "NODE3000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000013");
            break;
        case "NODE3000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000017");
            break;
        case "NODE3000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000018");
            break;
        case "NODE3000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000019");
            break;
        case "P4000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P4000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P4000003");
            break;
        case "P4000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P4000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P4000006");
            break;
        case "P6000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000002");
            break;
        case "P6000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000003");
            break;
        case "P6000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000006");
            break;
        case "RUSSEG000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000002");
            break;
        case "RUSSEG000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000003");
            break;
        case "RUSSEG000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000004");
            break;
        case "RUSSEG000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000005");
            break;
        case "RUSSEG000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000006");
            break;
        case "RUSSEG000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000007");
            break;
        case "RUSSEG000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000008");
            break;
        case "RUSSEG000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000009");
            break;
        case "RUSSEG000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000010");
            break;
        case "RUSSEG000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000011");
            break;
        case "RUSSEG000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000012");
            break;
        case "RUSSEG000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000013");
            break;
        case "RUSSEG000014":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000014");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000014");
            break;
        case "RUSSEG000015":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000015");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000015");
            break;
        case "RUSSEG000016":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000016");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000016");
            break;
        case "RUSSEG000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000017");
            break;
        case "RUSSEG000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000018");
            break;
        case "RUSSEG000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000019");
            break;
        case "RUSSEG000020":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000020");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000020");
            break;
        case "RUSSEG000021":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000021");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000021");
            break;
        case "RUSSEG000022":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000022");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000022");
            break;
        case "RUSSEG000023":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000023");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000023");
            break;
        case "RUSSEG000024":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000024");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000024");
            break;
        case "RUSSEG000025":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000025");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000025");
            break;
        case "S0000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000005");
            break;
        case "S0000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000010");
            break;
        case "S0000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000011");
            break;
        case "S0000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000012");
            break;
        case "S0000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000013");
            break;
        case "S1000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000006");
            break;
        case "S1000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000007");
            break;
        case "S1000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000008");
            break;
        case "S4000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S4000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S4000003");
            break;
        case "S4000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S4000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S4000006");
            break;
        case "S6000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S6000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S6000003");
            break;
        case "S6000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S6000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S6000006");
            break;
        case "TIME_000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "TIME_000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "TIME_000001");
            break;
        case "TIME_000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "TIME_000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "TIME_000002");
            break;
        case "USLAB000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000001");
            break;
        case "USLAB000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000002");
            break;
        case "USLAB000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000003");
            break;
        case "USLAB000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000004");
            break;
        case "USLAB000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000005");
            break;
        case "USLAB000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000006");
            break;
        case "USLAB000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000007");
            break;
        case "USLAB000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000008");
            break;
        case "USLAB000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000009");
            break;
        case "USLAB000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000010");
            break;
        case "USLAB000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000011");
            break;
        case "USLAB000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000013");
            break;
        case "USLAB000014":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000014");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000014");
            break;
        case "USLAB000015":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000015");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000015");
            break;
        case "USLAB000016":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000016");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000016");
            break;
        case "USLAB000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000017");
            break;
        case "USLAB000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000018");
            break;
        case "USLAB000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000019");
            break;
        case "USLAB000020":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000020");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000020");
            break;
        case "USLAB000021":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000021");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000021");
            break;
        case "USLAB000022":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000022");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000022");
            break;
        case "USLAB000023":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000023");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000023");
            break;
        case "USLAB000024":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000024");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000024");
            break;
        case "USLAB000025":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000025");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000025");
            break;
        case "USLAB000026":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000026");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000026");
            break;
        case "USLAB000027":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000027");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000027");
            break;
        case "USLAB000028":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000028");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000028");
            break;
        case "USLAB000029":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000029");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000029");
            break;
        case "USLAB000030":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000030");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000030");
            break;
        case "USLAB000031":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000031");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000031");
            break;
        case "USLAB000038":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000038");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000038");
            break;
        case "USLAB000040":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000040");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000040");
            break;
        case "USLAB000041":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000041");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000041");
            break;
        case "USLAB000042":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000042");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000042");
            break;
        case "USLAB000043":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000043");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000043");
            break;
        case "USLAB000044":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000044");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000044");
            break;
        case "USLAB000045":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000045");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000045");
            break;
        case "USLAB000046":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000046");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000046");
            break;
        case "USLAB000047":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000047");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000047");
            break;
        case "USLAB000048":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000048");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000048");
            break;
        case "USLAB000049":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000049");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000049");
            break;
        case "USLAB000050":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000050");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000050");
            break;
        case "USLAB000051":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000051");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000051");
            break;
        case "USLAB000052":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000052");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000052");
            break;
        case "USLAB000053":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000053");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000053");
            break;
        case "USLAB000054":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000054");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000054");
            break;
        case "USLAB000055":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000055");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000055");
            break;
        case "USLAB000056":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000056");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000056");
            break;
        case "USLAB000057":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000057");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000057");
            break;
        case "USLAB000058":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000058");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000058");
            break;
        case "USLAB000059":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000059");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000059");
            break;
        case "USLAB000060":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000060");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000060");
            break;
        case "USLAB000061":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000061");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000061");
            break;
        case "USLAB000062":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000062");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000062");
            break;
        case "USLAB000063":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000063");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000063");
            break;
        case "USLAB000064":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000064");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000064");
            break;
        case "USLAB000065":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000065");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000065");
            break;
        case "USLAB000066":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000066");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000066");
            break;
        case "USLAB000067":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000067");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000067");
            break;
        case "USLAB000068":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000068");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000068");
            break;
        case "USLAB000069":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000069");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000069");
            break;
        case "USLAB000070":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000070");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000070");
            break;
        case "USLAB000071":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000071");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000071");
            break;
        case "USLAB000072":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000072");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000072");
            break;
        case "USLAB000073":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000073");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000073");
            break;
        case "USLAB000074":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000074");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000074");
            break;
        case "USLAB000075":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000075");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000075");
            break;
        case "USLAB000076":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000076");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000076");
            break;
        case "USLAB000077":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000077");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000077");
            break;
        case "USLAB000078":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000078");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000078");
            break;
        case "USLAB000079":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000079");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000079");
            break;
        case "USLAB000080":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000080");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000080");
            break;
        case "USLAB000081":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000081");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000081");
            break;
        case "USLAB000082":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000082");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000082");
            break;
        case "USLAB000083":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000083");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000083");
            break;
        case "USLAB000084":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000084");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000084");
            break;
        case "USLAB000085":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000085");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000085");
            break;
        case "USLAB000087":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000087");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000087");
            break;
        case "USLAB000088":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000088");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000088");
            break;
        case "USLAB000089":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000089");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000089");
            break;
        case "USLAB000090":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000090");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000090");
            break;
        case "USLAB000091":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000091");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000091");
            break;
        case "USLAB000093":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000093");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000093");
            break;
        case "USLAB000094":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000094");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000094");
            break;
        case "USLAB000095":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000095");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000095");
            break;
        case "USLAB000096":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000096");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000096");
            break;
        case "USLAB000097":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000097");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000097");
            break;
        case "USLAB000098":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000098");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000098");
            break;
        case "USLAB000099":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000099");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000099");
            break;
        case "USLAB000100":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000100");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000100");
            break;
        case "USLAB000101":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000101");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000101");
            break;
        case "USLAB000102":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000102");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000102");
            break;
        case "Z1000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000001");
            break;
        case "Z1000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000002");
            break;
        case "Z1000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000003");
            break;
        case "Z1000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000004");
            break;
        case "Z1000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000005");
            break;
        case "Z1000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000006");
            break;
        case "Z1000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000007");
            break;
        case "Z1000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000008");
            break;
        case "Z1000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000009");
            break;
        case "Z1000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000010");
            break;
        case "Z1000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000011");
            break;
        case "Z1000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000012");
            break;
    }
  }
});

timeSub.addListener({
  onItemUpdate: function (update) {
        var status = update.getValue("Status.Class");
        AOStimestamp = parseFloat(update.getValue("TimeStamp"));
        //console.log("Timestamp: " + update.getValue("TimeStamp"));
        difference = timestampnow - AOStimestamp;
        //console.log("Difference " + difference);

    if ( status === "24")
    {
        if( difference > 0.00153680542553047 )
        {
            console.log("Signal Error!     @ " + update.getValue("TimeStamp"));
            AOS = "Stale Signal";
            AOSnum = 2;
        }
        else
        {
            if ( AOSnum !== 1 )
            {
               console.log("Connected to the ISS!     @ " + update.getValue("TimeStamp"));
            }
            AOS = "Siqnal Acquired";
            AOSnum = 1;
        }
    }
    else
    {
        console.log("Signal Lost!     @ " + update.getValue("TimeStamp"));
        AOS = "Signal Lost";
        AOSnum = 0;
    }
    db.run("UPDATE telemetry set Value = ? where Label = ?", AOSnum, "aos");
    db.run("UPDATE telemetry set Timestamp = ? where Label = ?", AOStimestamp, "aos");
  }
});
