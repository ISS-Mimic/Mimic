import kivy
import sched, time
import time
import os
import math
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
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, WipeTransition, SwapTransition

new_x = 0
new_y = 0

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
class CalibrateScreen(Screen):
    def __init__(self, **kwargs):
        super(CalibrateScreen, self).__init__(**kwargs)

    def zeroJoints(self):
        self.changeBoolean(True)

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
   
class FakeOrbitScreen(Screen):
    def __init__(self, **kwargs):
        super(FakeOrbitScreen, self).__init__(**kwargs)

class MimicScreen(Screen, EventDispatcher):
    def __init__(self, **kwargs):
        super(MimicScreen, self).__init__(**kwargs)

class MainScreenManager(ScreenManager):
    pass

class MyButton(Button):
    pass

class MainApp(App):

    def build(self):
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')
        self.main_screen = MainScreen(name = 'main')
        root = ScreenManager(transition=WipeTransition())
        #root.add_widget(MainScreen(name = 'main'))
        root.add_widget(CalibrateScreen(name = 'calibrate'))
        root.add_widget(self.mimic_screen)
        root.add_widget(self.main_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(ManualControlScreen(name = 'manualcontrol'))
        root.current = 'main'
        Clock.schedule_interval(self.animate,0.1)
        return root
    
    def animate(self, instance):
        global new_x
        global new_y
        print new_y
        new_x = new_x+0.01
        new_y = (math.sin(new_x*10)/5)+0.4
        if new_x > 0.8:
            new_x = 0
            new_y = 0
        self.main_screen.ids.ISStiny.pos_hint = {"center_x": new_x, "center_y": new_y}

    
Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
<MainScreen>:
    name: 'main'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/ISSmimicLogoPartsGroundtrack.png'
            allow_stretch: True
            keep_ratio: True
        Image:
            #canvas.after:
            id: ISStiny
            source: './imgs/ISSmimicLogoPartsGlowingISS.png'
            keep_ratio: False
            allow_stretch: True
            size_hint: 0.1,0.1
            #pos: 5000,500
            pos_hint: {"center_x": 0.25, "center_y": 0.25}
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
                      
''')

if __name__ == '__main__':
    MainApp().run()

#runTouchApp(root_widget)
