import kivy
import sqlite3
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

bus = smbus.SMBus(1)
address = 0x04

psarj = 0.00

p = multiprocessing.Process(target = muterun_js,args=('iss_telemetry.js',))

conn = sqlite3.connect('iss_telemetry.db')
c = conn.cursor()

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
class CalibrateScreen(Screen):
    pass

class ManualControlScreen(Screen):
    def __init__(self, **kwargs):
        super(ManualControlScreen, self).__init__(**kwargs)

class MimicScreen(Screen, EventDispatcher):
    def __init__(self, **kwargs):
        super(MimicScreen, self).__init__(**kwargs)

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
        print "colordown1"
        self.triangle_color = (1,0,1,1)

    def changecolorup(self, *args):
        print "colorup1"
        self.triangle_color = (1,0,0,1)

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3) 

class MainApp(App):
    def build(self):
        self.mimic_screen = MimicScreen(name = 'mimic')
        root = ScreenManager(transition=WipeTransition())
        root.add_widget(MainScreen(name = 'main'))
        root.add_widget(CalibrateScreen(name = 'calibrate'))
        root.add_widget(self.mimic_screen)
        root.add_widget(ManualControlScreen(name = 'manualcontrol'))
        root.current= 'main'
    
        Clock.schedule_interval(self.update_labels, 1)
        return root

    def update_labels(self, dt):
        c.execute('SELECT two FROM telemetry where one="psarj"')
        psarj = c.fetchone()
        print psarj[0]
        #assert type(psarj[0]) is str
        self.mimic_screen.ids.psarjvalue.text =str(psarj[0])

    def startTelemetry(*kwargs):
        sp.start()

    def stopTelemetry(*kwargs):
        os.kill(p.pid,signal.SIGKILL)

Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
<MainScreen>:
    name: 'main'
    FloatLayout:
        orientation: 'vertical'

        Image:
            source: 'iss.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            text: 'Main Screen'
            bold: True
            font_size: 120
            markup: True
            height: "20dp"
            color: 1,0,1
            width: "100dp"
        BoxLayout:
            size_hint_y: None
            Button:
                text: 'Control'
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'manualcontrol'
            Button:
                text: 'Calibrate'
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'calibrate'
                on_release: my_button.disabled = False
            Button:
                text: 'Exit'
                font_size: 30
                width: 50
                height: 20
                on_release: app.stop(*args)
            MyButton:
                id: my_button
                text: 'Mimic'
                disabled: True
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'mimic'

<ManualControlScreen>:
    name: 'manualcontrol'
    FloatLayout:
        Image:
            source: 'iss2.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            size_hint: None,None
            text: '1B'
            pos: root.width*.5, root.width*.5
            font_size: 30
            halign: 'center'
            valign: 'middle'
        TriangleButton:
            id: t1Bup
            p1: root.width*0.060, root.height*0.86
            p2: root.width*0.095, root.height*0.96
            p3: root.width*0.130, root.height*0.86
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Bdown
            p1: root.width*0.060, root.height*0.8
            p2: root.width*0.095, root.height*0.7
            p3: root.width*0.130, root.height*0.8
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3B'
            pos: root.width*.035, root.width*.18
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Bup
            p1: root.width*0.060, root.height*0.36
            p2: root.width*0.095, root.height*0.46
            p3: root.width*0.130, root.height*0.36
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Bdown
            p1: root.width*0.060, root.height*0.3
            p2: root.width*0.095, root.height*0.2
            p3: root.width*0.130, root.height*0.3
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3A'
            pos_hint: {'x': .155, 'y': .75}
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Aup
            p1: root.width*0.180, root.height*0.86
            p2: root.width*0.215, root.height*0.96
            p3: root.width*0.250, root.height*0.86
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Adown
            p1: root.width*0.180, root.height*0.8
            p2: root.width*0.215, root.height*0.7
            p3: root.width*0.250, root.height*0.8
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '1A'
            pos_hint: {'x': .155, 'y': .25}
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t1Aup
            p1: root.width*0.180, root.height*0.36
            p2: root.width*0.215, root.height*0.46
            p3: root.width*0.250, root.height*0.36
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Adown
            p1: root.width*0.180, root.height*0.3
            p2: root.width*0.215, root.height*0.2
            p3: root.width*0.250, root.height*0.3
            on_press: self.changecolordown()
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'SSARJ'
            pos_hint: {'x': .275, 'y': .5}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: 'STTRJ'
            pos_hint: {'x': .445, 'y': .55}
            font_size: 30
            halign: 'center'
            valign: 'middle'
        Label:
            size_hint: None,None
            text: 'PTTRJ'
            pos_hint: {'x': .445, 'y': .45}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: 'PSARJ'
            pos_hint: {'x': .6, 'y': .5}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: '2A'
            pos_hint: {'x': .715, 'y': .75}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: '4A'
            pos_hint: {'x': .715, 'y': .25}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: '4B'
            pos_hint: {'x': .84, 'y': .75}
            font_size: 30
            halign: 'center'
        Label:
            size_hint: None,None
            text: '2B'
            pos_hint: {'x': .84, 'y': .25}
            font_size: 30
            halign: 'center'
        Button:
            size_hint_y: None
            text: 'Return'
            font_size: 30
            on_release: root.manager.current = 'main'
            
<CalibrateScreen>:
    name: 'calibrate'
    FloatLayout:
        orientation: 'vertical'
        
        Image:
            source: 'iss_calibrate.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.5, "center_y": 0.97}
            id: calibratestatus
            text: 'Calibrate ISS Angles'
            color: 0,0,0,1
            font_size: 40
        Button:
            size_hint: 0.4,0.1
            pos_hint: {"center_x": 0.5, "center_y": 0.25}
            text: 'Zero SARJs'
            font_size: 30
            on_release: calibratestatus.text = 'SARJ angles zeroed'
        Button:
            size_hint: 0.4,0.1
            pos_hint: {"center_x": 0.5, "center_y": 0.65}
            text: 'Zero BGAs'
            font_size: 30
            on_release: calibratestatus.text = 'BGA angles zeroed'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"right": 1, "bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.manager.current = 'main'
<MimicScreen>:
    name: 'mimic'
    FloatLayout:
        psarjvalue: psarjvalue
        id: mimicscreenlayout
        Image:
            source: 'iss1.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            id: psarjvalue
            pos_hint: {"center_x": 0.7, "center_y": 0.5}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 60
        Label:
            id: telemetrystatus
            pos_hint: {"center_x": 0.6, "center_y": 0.8}
            text: 'Telemetry'
            markup: True
            color: 1,0,1
            font_size: 60
        Button:
            id: mimicstartbutton
            size_hint: 0.3,0.1
            pos_hint: {"x": 0.1, "y": 0.6}
            text: 'MIMIC'
            disabled: False
            font_size: 30
            on_release: telemetrystatus.text = 'Fetching Telemetry...'
            on_release: app.startTelemetry()
            on_release: mimicstopbutton.disabled = False
            on_release: mimicstartbutton.disabled = True
        Button:
            id: mimicstopbutton
            size_hint: 0.3,0.1
            pos_hint: {"x": 0.1, "y": 0.4}
            text: 'Stop'
            disabled: True
            font_size: 30
            on_release: telemetrystatus.text = 'Program Stopped'
            on_release: app.stopTelemetry()
            on_release: mimicstopbutton.disabled = True
            on_release: mimicstartbutton.disabled = False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
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
