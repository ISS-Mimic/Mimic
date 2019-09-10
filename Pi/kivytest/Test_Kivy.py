import os
os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason
import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.uix.gridlayout import GridLayout

class BubbleButton(Button):
    pass

class NumPad(Bubble):
    pass

class TestApp(App):
    pass

if __name__ == '__main__':
    TestApp().run()
