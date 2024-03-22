import re
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL

def get_mission(mission_str):
    return mission_str.split()[1] if len(mission_str.split(" ")) > 1 else mission_str

def get_spacecraft(mission_str):
    spacecraft_mapping = {
        "CRS": "SpaceX Dragon",
        "Crew": "SpaceX Dragon",
        "NG": "Northrop Grumman Cygnus",
        "Boeing": "Boeing CST-100 Starliner",
        "Progress": "Progress",
        "Soyuz": "Soyuz"
    }
    for key in spacecraft_mapping:
        if key in mission_str:
            return spacecraft_mapping[key]
    return mission_str.split('_')[0]

def get_port(port_str):
    port_mapping = {
        "zenith": " Zenith",
        "nadir": " Nadir",
        "forward": " Forward",
        "aft": " Aft"
    }
    port_location_mapping = {
        "Unity": "Node 1",
        "Harmony": "Node 2",
        "Zvezda": "Service Module",
        "Rassvet": "MRM-1",
        "Poisk": "MRM-2",
        "Prichal": "RS Node"
    }

    for key, value in port_mapping.items():
        if key in port_str:
            port_base = port_str.split(key)[0]
            return port_location_mapping.get(port_base, port_base) + value
    return port_str

def fetch_iss_data():
    wikiurl = "https://en.wikipedia.org/wiki/International_Space_Station"
    
    response = None
    try:
        response = requests.get(wikiurl)
    except Exception as e:
        print("Caught network error")
        print(e)

    if response and response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': "wikitable"})

        if table:
            headers = ["Spacecraft", "Country", "Type", "Mission", "Port", "Arrival Date", "Planned Departure"]
            table_data = []

            for tr in table.find_all('tr')[1:]:
                cells = tr.find_all('td')
                header_cells = tr.find_all('th')
                if len(cells) > 0:
                    mission_str = cells[1].get_text(strip=True)

                    country_img_tag = header_cells[1].find('img')
                    country_link_tag = country_img_tag.find_parent('a') if country_img_tag else None
                    country = country_link_tag.get('title') if country_link_tag else ""

                    row_data = {
                        "Spacecraft": get_spacecraft(mission_str),
                        "Country": country,
                        "Type": cells[0].get_text(strip=True),
                        "Mission": get_mission(mission_str),
                        "Port": get_port(cells[2].get_text(strip=True)),
                        "Arrival Date": cells[3].get_text(strip=True).split("[")[0],
                        "Planned Departure": cells[4].get_text(strip=True).split("[")[0]
                    }
                    table_data.append(row_data)

            return table_data
        else:
            print("Table with class 'wikitable' not found.")
            return None
    else:
        print("Failed to retrieve the webpage.")
        return None


def find_changes(current_data, previous_data):
    new_arrivals = []
    recent_departures = []

    current_spacecraft = {row['Spacecraft'] for row in current_data}
    previous_spacecraft = {row['Spacecraft'] for row in previous_data}

    # Check for new arrivals
    for current_row in current_data:
        if current_row['Spacecraft'] not in previous_spacecraft:
            new_arrivals.append(current_row)

    # Check for recent departures
    for previous_row in previous_data:
        if previous_row['Spacecraft'] not in current_spacecraft:
            recent_departures.append(previous_row)

    return new_arrivals, recent_departures

def format_message(iss_data, new_arrivals, recent_departures):

    print(new_arrivals)
    print(recent_departures)
    message = ""
    if new_arrivals or recent_departures:
        if new_arrivals:
            message += "**New Arrivals at the ISS:**\n"
            for arrival in new_arrivals:
                message += f"- {arrival['Spacecraft']} from {arrival['Country']} arrived at {arrival['Port']} on {arrival['Arrival Date']}.\n"

        if recent_departures:
            message += "\n**Recent Departures from the ISS:**\n"
            for departure in recent_departures:
                message += f"- {departure['Spacecraft']} departed from the ISS.\n"
        message += "\n"

    message += "**The Current ISS Visiting Vehicles are:**\n\n"
    message += "```\n"  # Start of code block for monospaced font
    message += "Spacecraft | Country | Type | Mission | Port | Arrival Date | Departure Date\n"
    message += "-"*97 + "\n"  # Adjust the number based on your table width

    for row in iss_data:
        message += f"{row['Spacecraft']} | {row['Country']} | {row['Type']} | {row['Mission']} | {row['Port']} | {row['Arrival Date']} | {row['Planned Departure']}\n"

    message += "```"  # End of code block


    return message

def send_discord_message(iss_data, new_arrivals, recent_departures):
    global discord_webhook_url
    """Send the crew information as a single message."""
    formatted_info = format_message(iss_data, new_arrivals, recent_departures)
    data = {'content': formatted_info}
    response = requests.post(discord_webhook_url, json=data)
    return response.status_code

def main():
    global discord_webhook_url
    
    #discord_webhook_url = TEST_WEBHOOK_URL
    discord_webhook_url = MIMIC_WEBHOOK_URL
    
    # Load previous data if exists
    if os.path.exists('VV_previous_data.json'):
        with open('VV_previous_data.json', 'r') as f:
            previous_data = json.load(f)
    else:
        previous_data = []

    # Fetch current data
    current_data = fetch_iss_data()
    
    # For testing only
    #with open('VV_current_data.json', 'r') as f:
    #    current_data = json.load(f)

    # Compare and send message if changed
    if current_data != previous_data:
        new_arrivals, recent_departures = find_changes(current_data, previous_data)
        send_discord_message(current_data, new_arrivals, recent_departures)
        with open('VV_previous_data.json', 'w') as f:
            json.dump(current_data, f)

    # Wait for 15 minutes and then check again
    next_check_time = datetime.now() + timedelta(minutes=15)
    #next_check_time = datetime.now() + timedelta(seconds=30)

    while True:
        if datetime.now() >= next_check_time:
            main()

if __name__ == "__main__":
    main()

