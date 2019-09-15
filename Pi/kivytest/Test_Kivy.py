import os
os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason
from kivy.app import App

class TestApp(App):
    pass

if __name__ == '__main__':
    TestApp().run()
