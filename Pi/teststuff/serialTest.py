import serial
import serial.tools.list_ports

myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
print(myports)
ser = serial.Serial('/dev/ttyACM0',9600,timeout=0)
ser2 = serial.Serial('/dev/ttyAMA00',9600,timeout=0)
#ser2.close()
#print(ser.inWaiting())
#print(ser2.inWaiting())

#ser.open()
#ser.write(str.encode("a"))
try:
    ser.inWaiting()
except Exception:
    print("no ser1")
else:
    ser.write(str.encode("a"))
    print("ser 1 success")
try:
    ser2.inWaiting()
except Exception:
    print("no ser2")
else:
    ser2.write(str.encode("a"))
    print("ser 2 success")


#try:
#    while 1:
#        response = ser.readline()
#        print(response)
#except KeyboardInterrupt:
#    ser.close()
