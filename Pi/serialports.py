import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(p)
    #print(p.description)
    #print(p.device)
    print(p.hwid)
