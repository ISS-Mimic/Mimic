
    
    def getTLE(self, *args):
        global tle_rec, line1, line2, TLE_acquired
        iss_tle_url =  'https://blogs.nasa.gov/spacestation/tag/spacewalk'
        
        def on_success(req, data): #if TLE data is successfully received, it is processed here
            global tle_rec, line1, line2, TLE_acquired
            def process_tag_text(tag_text): #this function splits up the data received into proper TLE format
                firstTLE = True
                marker = 'TWO LINE MEAN ELEMENT SET'
                text = iter(tag_text.split('\n'))
                for line in text:
                    if (marker in line) and firstTLE:
                        firstTLE = False
                        next(text)
                        results.append('\n'.join(
                            (next(text), next(text), next(text))))
                return results
            logWrite("ISS TLE - Successfully fetched TLE page")
            soup = BeautifulSoup(data, 'html.parser')
            body = soup.find_all("pre")
            results = []
            for tag in body:
                if "ISS" in tag.text:
                    results.extend(process_tag_text(tag.text))

            if len(results) > 0:
                parsed = str(results[0]).split('\n')
                line1 = parsed[1]
                line2 = parsed[2]
                print(line1)
                print(line2)
                tle_rec = ephem.readtle("ISS (ZARYA)", str(line1), str(line2))
                TLE_acquired = True
                print("TLE Success!")
            else:
                print("TLE not acquired")
                TLE_acquired = False

        def on_redirect(req, result):
            logWrite("Warning - Get TLE failure (redirect)")

        def on_failure(req, result):
            logWrite("Warning - Get TLE failure (url failure)")

        def on_error(req, result):
            logWrite("Warning - Get TLE failure (url error)")
        
        req = UrlRequest(iss_tle_url, on_success, on_redirect, on_failure, on_error, timeout=1)

