import kivy
import sqlite3
import serial
import sched, time
import smbus
import time
from Naked.toolshed.shell import execute_js, muterun_js
import os
import signal
import multiprocessing, signal
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, WipeTransition, SwapTransition

fileplog = open('psarjlog.txt','w')


try:
    ser = serial.Serial('/dev/ttyUSB0', 115200)
except:
    print "Serial connection error"

mimicbutton = False
fakeorbitboolean = False
zerocomplete = False
switchtofake = False
manualcontrol = False

conn = sqlite3.connect('iss_telemetry.db') #sqlite database call change to include directory
c = conn.cursor() 
val = ""
    
psarj2 = 1.0
ssarj2 = 1.0

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
aos = 0.00

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

def StringToBytes(val):
    retVal = []
    for c in val:
            retVal.append(ord(c))
    return retVal

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
    
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
        
class CalibrateScreen(Screen):
    def __init__(self, **kwargs):
        super(CalibrateScreen, self).__init__(**kwargs)
   
    def serialWrite(self, *args):
        ser.write(*args)

    def zeroJoints(self):
        self.changeBoolean(True)
        ser.write('Zero')

    def changeBoolean(self, *args):
        global zerocomplete
        zerocomplete = args[0]

class ManualControlScreen(Screen):
    def __init__(self, **kwargs):
        super(ManualControlScreen, self).__init__(**kwargs)
    
    def incrementPSARJ(self, *args):
        global psarjmc
        psarjmc += args[0]
        self.serialWrite("PSARJ=" + str(psarjmc) + " ")   
     
    def incrementSSARJ(self, *args):
        global ssarjmc
        ssarjmc += args[0]
        self.serialWrite("SSARJ=" + str(ssarjmc) + " ")   
     
    def incrementPTTRJ(self, *args):
        global ptrrjmc
        ptrrjmc += args[0]
        self.serialWrite("PTRRJ=" + str(ptrrjmc) + " ")   
     
    def incrementSTRRJ(self, *args):
        global strrjmc
        strrjmc += args[0]
        self.serialWrite("STRRJ=" + str(strrjmc) + " ")   
     
    def incrementBeta1B(self, *args):
        global beta1bmc
        beta1bmc += args[0]
        self.serialWrite("Beta1B=" + str(beta1bmc) + " ")   
     
    def incrementBeta1A(self, *args):
        global beta1amc
        beta1amc += args[0]
        self.serialWrite("Beta1A=" + str(beta1amc) + " ")   
     
    def incrementBeta2B(self, *args):
        global beta2bmc
        beta2bmc += args[0]
        self.serialWrite("Beta2B=" + str(beta2bmc) + " ")   
     
    def incrementBeta2A(self, *args):
        global beta2amc
        beta2amc += args[0]
        self.serialWrite("Beta2A=" + str(beta2amc) + " ")   
     
    def incrementBeta3B(self, *args):
        global beta3bmc
        beta3bmc += args[0]
        self.serialWrite("Beta3B=" + str(beta3bmc) + " ")   
     
    def incrementBeta3A(self, *args):
        global beta3amc
        beta3amc += args[0]
        self.serialWrite("Beta3A=" + str(beta3amc) + " ")   
     
    def incrementBeta4B(self, *args):
        global beta4bmc
        beta4bmc += args[0]
        self.serialWrite("Beta4B=" + str(beta4bmc) + " ")   
     
    def incrementBeta4A(self, *args):
        global beta4amc
        beta4amc += args[0]
        self.serialWrite("Beta4A=" + str(beta4amc) + " ")   
     
    def changeBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
    
    def serialWrite(self, *args):
        ser.write(*args)
   
class FakeOrbitScreen(Screen):
    def __init__(self, **kwargs):
        super(FakeOrbitScreen, self).__init__(**kwargs)

    def serialWrite(self, *args):
        ser.write(*args)
    
    def changeBoolean(self, *args):
        global fakeorbitboolean
        global switchtofake
        switchtofake = args[0]
        fakeorbitboolean = args[0]

class MimicScreen(Screen, EventDispatcher):
    def __init__(self, **kwargs):
        super(MimicScreen, self).__init__(**kwargs)
   
    def changeMimicBoolean(self, *args):
        global mimicbutton
        mimicbutton = args[0]
    
    def changeSwitchBoolean(self, *args):
        global switchtofake
        switchtofake = args[0]

class MainScreenManager(ScreenManager):
    pass

class MyButton(Button):
    pass

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x = poly[0]
    p1y = poly[1]
    for i in range(0, n + 2, 2):
        p2x = poly[i % n]
        p2y = poly[(i + 1) % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class TriangleButton(ButtonBehavior, Widget):
    triangle_color = ListProperty([1,0,0,1])
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])

    def changecolordown(self, *args):
        self.triangle_color = (1,0,1,1)

    def changecolorup(self, *args):
        self.triangle_color = (1,0,0,1)

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3) 

class MainApp(App):

    def build(self):
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')

        root = ScreenManager(transition=WipeTransition())
        root.add_widget(MainScreen(name = 'main'))
        root.add_widget(CalibrateScreen(name = 'calibrate'))
        root.add_widget(self.mimic_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(ManualControlScreen(name = 'manualcontrol'))
        root.current= 'main'
    
        Clock.schedule_interval(self.update_labels, 1)
        return root

    def serialWrite(self, *args):
        ser.write(*args)

    def changeColors(self, *args):   #this function sets all labels on mimic screen to a certain color based on signal status
        self.mimic_screen.ids.psarjvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.ssarjvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.ptrrjvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.strrjvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta1avalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta1bvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta2avalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta2bvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta3avalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta3bvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta4avalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.beta4bvalue.color = args[0],args[1],args[2]
        self.mimic_screen.ids.aosvalue.color = args[0],args[1],args[2]
    
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
    
    def update_labels(self, dt):
        global mimicbutton
        global switchtofake
        global fakeorbitboolean
        global psarj2
        global ssarj2
        global manualcontrol
        global psarj
        global ssarj
        global ptrrj
        global strrj
        global beta1b
        global beta1a
        global beta2b
        global beta2a
        global beta3b
        global beta3a
        global beta4b
        global beta4a
        global aos
        global psarjmc
        global ssarjmc
        global ptrrjmc
        global strrjmc
        global beta1bmc
        global beta1amc
        global beta2bmc
        global beta2amc
        global beta3bmc
        global beta3amc
        global beta4bmc
        global beta4amc

        c.execute('select two from telemetry')
        values = c.fetchall()
        c.execute('select timestamp from telemetry')
        timestamps = c.fetchall()

        psarj = "{:.2f}".format((values[0])[0])
        if switchtofake == False:
            psarj2 = float(psarj)
        if manualcontrol == False:
            psarjmc = float(psarj)
        ssarj = "{:.2f}".format((values[1])[0])
        if switchtofake == False:
            ssarj2 = float(ssarj)
        if manualcontrol == False:
            ssarjmc = float(ssarj)
        ptrrj = "{:.2f}".format((values[2])[0])
        if manualcontrol == False:
            ptrrjmc = float(ptrrj)
        strrj = "{:.2f}".format((values[3])[0])
        if manualcontrol == False:
            strrjmc = float(strrj)
        beta1b = "{:.2f}".format((values[4])[0])
        if manualcontrol == False:
            beta1bmc = float(beta1b)
        beta1a = "{:.2f}".format((values[5])[0])
        if manualcontrol == False:
            beta1amc = float(beta1a)
        beta2b = "{:.2f}".format((values[6])[0])
        if manualcontrol == False:
            beta2bmc = float(beta2b)
        beta2a = "{:.2f}".format((values[7])[0])
        if manualcontrol == False:
            beta2amc = float(beta2a)
        beta3b = "{:.2f}".format((values[8])[0])
        if manualcontrol == False:
            beta3bmc = float(beta3b)
        beta3a = "{:.2f}".format((values[9])[0])
        if manualcontrol == False:
            beta3amc = float(beta3a)
        beta4b = "{:.2f}".format((values[10])[0])
        if manualcontrol == False:
            beta4bmc = float(beta4b)
        beta4a = "{:.2f}".format((values[11])[0])
        if manualcontrol == False:
            beta4amc = float(beta4a)
        aos = "{:.2f}".format(int((values[12])[0]))
        
        fileplog.write("PSARJ " + psarj)
        fileplog.write('\n')
        fileplog.write("SSARJ " + ssarj)
        fileplog.write('\n')
        fileplog.write("PTRRJ " + ptrrj)
        fileplog.write('\n')
        fileplog.write("STRRJ " + strrj)
        fileplog.write('\n')
        fileplog.write("Beta1A " + beta1a)
        fileplog.write('\n')
        fileplog.write("Beta1B " + beta1b)
        fileplog.write('\n')
        fileplog.write("Beta2A " + beta2a)
        fileplog.write('\n')
        fileplog.write("Beta2B " + beta2b)
        fileplog.write('\n')
        fileplog.write("Beta3A " + beta3a)
        fileplog.write('\n')
        fileplog.write("Beta3B " + beta3b)
        fileplog.write('\n')
        fileplog.write("Beta4A " + beta4a)
        fileplog.write('\n')
        fileplog.write("Beta4B " + beta4b)
        fileplog.write('\n')

        if (fakeorbitboolean == True and (mimicbutton == True or switchtofake == True)):
            if psarj2 <= 0.00:
                psarj2 = 360.0
            self.fakeorbit_screen.ids.fakepsarjvalue.text = "{:.2f}".format(psarj2)
            if ssarj2 >= 360.00:                
                ssarj2 = 0.0
            self.fakeorbit_screen.ids.fakessarjvalue.text = "{:.2f}".format(ssarj2)
            
            psarj2 -= 0.0666
            ssarj2 += 0.0666

            psarjstr = "{:.2f}".format(psarj2)
            ssarjstr = "{:.2f}".format(ssarj2)
            
            self.serialWrite("PSARJ=" + psarjstr + " ")
            self.serialWrite("SSARJ=" + ssarjstr + " ")
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
        
        self.mimic_screen.ids.psarjvalue.text = psarj
        self.mimic_screen.ids.ssarjvalue.text = ssarj
        self.mimic_screen.ids.ptrrjvalue.text = ptrrj
        self.mimic_screen.ids.strrjvalue.text = strrj
        self.mimic_screen.ids.beta1bvalue.text = beta1b
        self.mimic_screen.ids.beta1avalue.text = beta1a
        self.mimic_screen.ids.beta2bvalue.text = beta2b
        self.mimic_screen.ids.beta2avalue.text = beta2a
        self.mimic_screen.ids.beta3bvalue.text = beta3b
        self.mimic_screen.ids.beta3avalue.text = beta3a
        self.mimic_screen.ids.beta4bvalue.text = beta4b
        self.mimic_screen.ids.beta4avalue.text = beta4a

        if float(aos) == 1.00:
            self.changeColors(0,1,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = False
               if mimicbutton == True:
                   switchtofake = False
            self.mimic_screen.ids.aosvalue.text = "Signal Acquired!"
        elif float(aos) == 0.00:
            self.changeColors(1,0,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.mimic_screen.ids.aosvalue.text = "Signal Lost"
        elif float(aos) == 2.00:
            self.changeColors(1,0.5,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.mimic_screen.ids.aosvalue.text = "Stale Signal!"

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
 
Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
<MainScreen>:
    name: 'main'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            text: 'ISS Mimic'
            bold: True
            font_size: 120
            markup: True
            height: "20dp"
            color: 1,0,1
            width: "100dp"
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.2, "center_y": 0.9}
            text: 'Fake Orbit'
            font_size: 30
            width: 50
            height: 20
            on_release: root.manager.current = 'fakeorbit'
        BoxLayout:
            size_hint_y: None
            Button:
                text: 'Control'
                font_size: 30
                width: 50
                height: 20
                on_press: root.changeManualControlBoolean(True)
                on_release: root.manager.current = 'manualcontrol'
            Button:
                text: 'Calibrate'
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'calibrate'
                on_release: my_button.disabled = False
            MyButton:
                id: my_button
                text: 'Mimic'
                disabled: True
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'mimic'
            Button:
                text: 'Exit'
                font_size: 30
                width: 50
                height: 20
                on_release: app.stop(*args)
<FakeOrbitScreen>:
    name: 'fakeorbit'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            id: fakeorbitstatus
            pos_hint: {"center_x": 0.25, "center_y": 0.85}
            text: 'Status'
            markup: True
            color: 1,0,1
            font_size: 60
        Label:
            id: fakepsarjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.5}
            text: 'PSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakepsarjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.5}
            text: '0.000'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakessarjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.35}
            text: 'SSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakessarjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.35}
            text: '0.000'
            markup: True
            color: 1,1,1
            font_size: 30
        Button:
            id: orbitstartbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.6}
            text: 'Start'
            disabled: False
            font_size: 30
            on_release: fakeorbitstatus.text = 'Sending...'
            on_release: root.changeBoolean(True)
            on_release: orbitstopbutton.disabled = False
            on_release: orbitstartbutton.disabled = True
        Button:
            id: orbitstopbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.4}
            text: 'Stop'
            disabled: True
            font_size: 30
            on_release: fakeorbitstatus.text = 'Stopped'
            on_release: root.changeBoolean(False)
            on_release: orbitstopbutton.disabled = True
            on_release: orbitstartbutton.disabled = False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.changeBoolean(False)
            on_release: root.manager.current = 'main'
           
<ManualControlScreen>:
    name: 'manualcontrol'
    FloatLayout:
        Image:
            source: './imgs/iss_calibrate.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            size_hint: None,None
            text: '1B'
            pos_hint: {'x': 0.035, 'y': 0.73}
            font_size: 30
            markup: True
            color: 0,0,0,1
            halign: 'center'
            valign: 'middle'
        TriangleButton:
            id: t1Bup
            p1: root.width*0.060, root.height*0.86
            p2: root.width*0.095, root.height*0.96
            p3: root.width*0.130, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Bdown
            p1: root.width*0.060, root.height*0.8
            p2: root.width*0.095, root.height*0.7
            p3: root.width*0.130, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3B'
            pos_hint: {'x': 0.035, 'y': 0.25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Bup
            p1: root.width*0.060, root.height*0.38
            p2: root.width*0.095, root.height*0.48
            p3: root.width*0.130, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta3B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Bdown
            p1: root.width*0.060, root.height*0.32
            p2: root.width*0.095, root.height*0.22
            p3: root.width*0.130, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta3B(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3A'
            pos_hint: {'x': .155, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Aup
            p1: root.width*0.180, root.height*0.86
            p2: root.width*0.215, root.height*0.96
            p3: root.width*0.250, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta3A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Adown
            p1: root.width*0.180, root.height*0.8
            p2: root.width*0.215, root.height*0.7
            p3: root.width*0.250, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta3A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '1A'
            pos_hint: {'x': .155, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t1Aup
            p1: root.width*0.180, root.height*0.38
            p2: root.width*0.215, root.height*0.48
            p3: root.width*0.250, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta1A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Adown
            p1: root.width*0.180, root.height*0.32
            p2: root.width*0.215, root.height*0.22
            p3: root.width*0.250, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta1A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'SSARJ'
            pos_hint: {'x': .275, 'y': .5}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: SSARJup
            p1: root.width*0.300, root.height*0.65
            p2: root.width*0.335, root.height*0.75
            p3: root.width*0.370, root.height*0.65
            on_press: self.changecolordown()
            on_release: root.incrementSSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: SSARJdown
            p1: root.width*0.300, root.height*0.55
            p2: root.width*0.335, root.height*0.45
            p3: root.width*0.370, root.height*0.55
            on_press: self.changecolordown()
            on_release: root.incrementSSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'STTRJ'
            pos_hint: {'x': .445, 'y': .55}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
            valign: 'middle'
        TriangleButton:
            id: STTRJup
            p1: root.width*0.480, root.height*0.800
            p2: root.width*0.420, root.height*0.750
            p3: root.width*0.480, root.height*0.700
            on_press: self.changecolordown()
            on_release: root.incrementSTRRJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: STTRJdown
            p1: root.width*0.520, root.height*0.800
            p2: root.width*0.580, root.height*0.750
            p3: root.width*0.520, root.height*0.700
            on_press: self.changecolordown()
            on_release: root.incrementSTRRJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'PTTRJ'
            pos_hint: {'x': .445, 'y': .45}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: PTTRJup
            p1: root.width*0.480, root.height*0.400
            p2: root.width*0.420, root.height*0.450
            p3: root.width*0.480, root.height*0.500
            on_press: self.changecolordown()
            on_release: root.incrementPTRRJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: PTTRJdown
            p1: root.width*0.520, root.height*0.400
            p2: root.width*0.580, root.height*0.450
            p3: root.width*0.520, root.height*0.500
            on_press: self.changecolordown()
            on_release: root.incrementPTRRJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'PSARJ'
            pos_hint: {'x': .6, 'y': .5}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: PSARJup
            p1: root.width*0.700, root.height*0.65
            p2: root.width*0.665, root.height*0.75
            p3: root.width*0.630, root.height*0.65
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: PSARJdown
            p1: root.width*0.700, root.height*0.55
            p2: root.width*0.665, root.height*0.45
            p3: root.width*0.630, root.height*0.55
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '2A'
            pos_hint: {'x': .725, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t2Aup
            p1: root.width*0.820, root.height*0.86
            p2: root.width*0.785, root.height*0.96
            p3: root.width*0.750, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta2A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t2Adown
            p1: root.width*0.820, root.height*0.8
            p2: root.width*0.785, root.height*0.7
            p3: root.width*0.750, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta2A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '4A'
            pos_hint: {'x': .725, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t4Aup
            p1: root.width*0.820, root.height*0.38
            p2: root.width*0.785, root.height*0.48
            p3: root.width*0.750, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta4A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t4Adown
            p1: root.width*0.820, root.height*0.32
            p2: root.width*0.785, root.height*0.22
            p3: root.width*0.750, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta4A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '4B'
            pos_hint: {'x': .84, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t4Bup
            p1: root.width*0.940, root.height*0.86
            p2: root.width*0.905, root.height*0.96
            p3: root.width*0.870, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta4B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t4Bdown
            p1: root.width*0.940, root.height*0.8
            p2: root.width*0.905, root.height*0.7
            p3: root.width*0.870, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta4B(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '2B'
            pos_hint: {'x': .84, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t2Bup
            p1: root.width*0.940, root.height*0.38
            p2: root.width*0.905, root.height*0.48
            p3: root.width*0.870, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta2B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t2Bdown
            p1: root.width*0.940, root.height*0.32
            p2: root.width*0.905, root.height*0.22
            p3: root.width*0.870, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta2B(-1)
            on_release: self.changecolorup()
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.5, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_press: root.changeBoolean(False)
            on_release: root.manager.current = 'main'
            
<CalibrateScreen>:
    name: 'calibrate'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss_calibrate.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.5, "center_y": 0.95}
            id: calibratestatus
            text: 'Calibrate ISS Angles'
            color: 0,0,0,1
            font_size: 40
        Button:
            id: zerobutton
            size_hint: 0.4,0.1
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            text: 'Zero All Angles'
            font_size: 30
            on_press: root.zeroJoints()
            on_release: calibratestatus.text = 'Angles Zero-ing!'
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.5, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.manager.current = 'main'
<MimicScreen>:
    name: 'mimic'
    FloatLayout:
        psarjvalue: psarjvalue
        id: mimicscreenlayout
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            id: telemetrystatus
            pos_hint: {"center_x": 0.25, "center_y": 0.85}
            text: 'Telemetry'
            markup: True
            color: 1,0,1
            font_size: 60
        Label:
            id: psarjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.92}
            text: 'PSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: psarjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.92}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: ssarjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.85}
            text: 'SSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: ssarjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.85}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: ptrrjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.78}
            text: 'PTRRJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: ptrrjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: strrjlabel
            pos_hint: {"center_x": 0.6, "center_y": 0.71}
            text: 'STRRJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: strrjvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta1blabel
            pos_hint: {"center_x": 0.6, "center_y": 0.64}
            text: 'Beta 1B:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta1bvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.64}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta1alabel
            pos_hint: {"center_x": 0.6, "center_y": 0.57}
            text: 'Beta 1A:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta1avalue
            pos_hint: {"center_x": 0.8, "center_y": 0.57}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta2blabel
            pos_hint: {"center_x": 0.6, "center_y": 0.50}
            text: 'Beta 2B:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta2bvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.50}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta2alabel
            pos_hint: {"center_x": 0.6, "center_y": 0.43}
            text: 'Beta 2A:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta2avalue
            pos_hint: {"center_x": 0.8, "center_y": 0.43}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta3blabel
            pos_hint: {"center_x": 0.6, "center_y": 0.36}
            text: 'Beta 3B:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta3bvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.36}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta3alabel
            pos_hint: {"center_x": 0.6, "center_y": 0.29}
            text: 'Beta 3A:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta3avalue
            pos_hint: {"center_x": 0.8, "center_y": 0.29}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta4blabel
            pos_hint: {"center_x": 0.6, "center_y": 0.22}
            text: 'Beta 4B:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta4bvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.22}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta4alabel
            pos_hint: {"center_x": 0.6, "center_y": 0.15}
            text: 'Beta 4A:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: beta4avalue
            pos_hint: {"center_x": 0.8, "center_y": 0.15}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: aoslabel
            pos_hint: {"center_x": 0.53, "center_y": 0.05}
            text: 'Signal Status:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: aosvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.05}
            text: ' '
            markup: True
            color: 1,1,1
            font_size: 30
        Button:
            id: mimicstartbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.6}
            text: 'MIMIC'
            disabled: False
            font_size: 30
            on_release: telemetrystatus.text = 'Sending...'
            on_release: root.changeMimicBoolean(True)
            on_release: mimicstopbutton.disabled = False
            on_release: mimicstartbutton.disabled = True
        Button:
            id: mimicstopbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.4}
            text: 'Stop'
            disabled: True
            font_size: 30
            on_release: telemetrystatus.text = 'Stopped'
            on_release: root.changeMimicBoolean(False)
            on_release: root.changeSwitchBoolean(False)
            on_release: mimicstopbutton.disabled = True
            on_release: mimicstartbutton.disabled = False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.changeMimicBoolean(False)
            on_release: root.changeSwitchBoolean(False)
            on_release: root.manager.current = 'main'
           
<TriangleButton>:
    canvas.after:
        Color:
            rgba: self.triangle_color
        Triangle:
            points: self.p1 + self.p2 + self.p3
            
''')

if __name__ == '__main__':
    MainApp().run()

#runTouchApp(root_widget)
