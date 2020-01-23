iss_tle_url =  'https://blogs.nasa.gov/spacestation/tag/spacewalk'

def on_success(req, data): #if TLE data is successfully received, it is processed here
    print("success")
    print(data)

def on_redirect(req, result):
    print("Warning - Get TLE failure (redirect)")

def on_failure(req, result):
    print("Warning - Get TLE failure (url failure)")

def on_error(req, result):
    print("Warning - Get TLE failure (url error)")

req = UrlRequest(iss_tle_url, on_success, on_redirect, on_failure, on_error, timeout=1)

