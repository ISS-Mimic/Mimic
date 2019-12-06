import os
os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason
from kivy.app import App
from kivy.network.urlrequest import UrlRequest #using this to request webpages
from bs4 import BeautifulSoup #used to parse webpages for data (EVA stats, ISS TLE)

class TestApp(App):
    iss_blog_url =  'https://www.celestrak.com/NORAD/elements/stations.txt'
    def on_success(req, data): #if TLE data is successfully received, it is processed here
        print("Blog Success")
        soup = BeautifulSoup(data, "lxml")
        body = iter(soup.get_text().split('\n'))
        results = []
        for line in body:
            if "ISS (ZARYA)" in line:
                results.append(line)
                results.append(next(body))
                results.append(next(body))
                break
        results = [i.strip() for i in results]
        print(results)

    def on_redirect(req, result):
        print("Warning - Get nasa blog failure (redirect)")

    def on_failure(req, result):
        print("Warning - Get nasa blog failure (url failure)")

    def on_error(req, result):
        print("Warning - Get nasa blog failure (url error)")

    req = UrlRequest(iss_blog_url, on_success, on_redirect, on_failure, on_error, timeout=1)

if __name__ == '__main__':
    TestApp().run()
