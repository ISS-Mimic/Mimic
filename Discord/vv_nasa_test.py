import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime, timedelta
import os
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL

def parse_date(date_str):
    """Parse a date string that could be in either two-digit or four-digit year format."""
    for date_format in ('%m/%d/%Y', '%m/%d/%y'):  # Try both formats
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    return None  # Return None if neither format works


def is_recent(date, max_age_years=2):
    """Check if the date is within the specified number of years from today."""
    if date is None:
        return False
    return datetime.now() - date < timedelta(days=max_age_years * 365)


def parse_vehicle_events(html_content):
    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all text containing vehicle events
    vehicle_events = soup.find_all(
        string=re.compile("SpaceX CRS|SpaceX Crew|ISS Progress|Cygnus|Dragon|Axiom Mission|Soyuz|Crew Dragon"))

    #print(vehicle_events)
    # Process each event
    events = {}
    for event in vehicle_events:

        event_text = event.strip()
        # Extract date and event type
        date_match = re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", event_text)
        event_date = parse_date(date_match.group(0)) if date_match else None

        if "Dock" in event_text or "Capture" in event_text:
            print("dock")
            event_type = "Dock/Capture"
        elif "Undock" in event_text or "Release" in event_text:
            event_type = "Undock/Release"
        else:
            event_type = "Launch"

        # Extracting the full vehicle name
        vehicle_name_match = re.search(
            r"(SpaceX CRS-\d+|SpaceX Crew-\d+|ISS Progress \d+|Cygnus \w+-\d+|Dragon \d+|Axiom Mission \d+|Soyuz MS-\d+|Crew Dragon \w+-\d+)",
            event_text)
        vehicle_name = vehicle_name_match.group(0) if vehicle_name_match else "Unknown Vehicle"

        # Store events in a dictionary
        if vehicle_name not in events:
            events[vehicle_name] = []
        events[vehicle_name].append((event_date, event_type))

    # Sorting events for each vehicle by date, handling None values
    for vehicle in events:
        events[vehicle].sort(key=lambda x: x[0] or datetime.min)

    return events


def find_current_vehicles(events):
    # Identify vehicles currently at the ISS
    print(events)
    current_vehicles = []
    for vehicle, vehicle_events in events.items():
        # Include vehicles whose most recent event is 'Dock/Capture' and have no 'Undock/Release' events
        if vehicle_events[-1][1] == 'Dock/Capture' and not any(
                event[1] == 'Undock/Release' for event in vehicle_events) and is_recent(vehicle_events[-1][0]):
            print(vehicle)
            vehicle = vehicle.replace("ISS ","")
            vehicle += "\n"
            current_vehicles.append(vehicle)
    return sorted(current_vehicles)

def find_iss_image(soup):
    """Find the ISS image based on a specific pattern."""
    images = soup.find_all('img')
    for img in images:
        if img.get('src') and re.search(r'iss.*\.png', img['src']):
            return img['src']
    return None


def download_image(image_url, save_path):
    """Download an image from the given URL and save it to the specified path."""
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
    return response.status_code == 200

def send_discord_notification_with_image(webhook_url, message, image_path):
    """Send a notification message along with an image to a Discord webhook."""
    files = {'file': (os.path.basename(image_path), open(image_path, 'rb'))}
    payload = {"content": message}
    response = requests.post(webhook_url, data=payload, files=files)
    return response.status_code

def save_to_json(filename, data):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_from_json(filename):
    """Load data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def send_discord_notification(webhook_url, message):
    """Send a notification message to a Discord webhook."""
    payload = {"content": message}
    response = requests.post(webhook_url, json=payload)
    return response.status_code


def detect_changes(old_list, new_list):
    """Detect which vehicles have docked or undocked."""
    old_set = set(old_list) if old_list else set()
    new_set = set(new_list)
    docked = new_set - old_set
    undocked = old_set - new_set
    return sorted(docked), sorted(undocked)


# Main program
def main():
    # URL of the NASA webpage
    url = "https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/"

    # File to save current vehicle data
    json_file = 'NASA_current_vehicles.json'

    #discord_webhook_url = TEST_WEBHOOK_URL
    discord_webhook_url = MIMIC_WEBHOOK_URL

    while True:
        # Fetch the webpage content
        response = requests.get(url)

        html_content = response.text

        #print(html_content)

        # Parse vehicle events
        events = parse_vehicle_events(html_content)

        # Find current vehicles at the ISS
        current_vehicles = find_current_vehicles(events)
        #print(current_vehicles)

        # Load previous data
        previous_vehicles = load_from_json(json_file)

        if current_vehicles is None:
            current_vehicles = []
        if previous_vehicles is None:
            previous_vehicles = []

        # Check if there is any change in the data
        if current_vehicles != previous_vehicles:
            print("diff")
            # Detect changes
            docked, undocked = detect_changes(previous_vehicles, current_vehicles)

            # Save new data to JSON file
            save_to_json(json_file, current_vehicles)

            # Find the ISS image from the NASA page
            soup = BeautifulSoup(html_content, "html.parser")
            iss_image_url = find_iss_image(soup)
            if iss_image_url:
                if not iss_image_url.startswith('http'):
                    # Handle relative URLs
                    iss_image_url = 'https://www.nasa.gov' + iss_image_url

                image_path = 'iss_image.png'  # Local path to save the image
                if download_image(iss_image_url, image_path):
                    print("ISS image downloaded successfully.")
                else:
                    print("Failed to download the ISS image.")

            # Send a notification if previous data exists
            #if previous_vehicles is not None:
            message = "Update: The list of visiting vehicles at the ISS has changed. \n \n"
            if docked:
                message += "**Docked/Berthed:** \n" + "".join(docked) + "\n"
            if undocked:
                message += "**Undocked/Unberthed:** \n" + "".join(undocked) + "\n"
            message += "**Current Vehicles at the ISS:** \n" + "".join(current_vehicles)
            #send_discord_notification(discord_webhook_url, message)
            send_discord_notification_with_image(discord_webhook_url, message, image_path)

            print(message)

        # Wait for 5 minutes before the next check
        time.sleep(300)


if __name__ == "__main__":
    main()

