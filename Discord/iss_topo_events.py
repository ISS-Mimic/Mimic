import requests
import re
import json
import schedule
import time
from datetime import datetime, timedelta
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL

#webhook_url = TEST_WEBHOOK_URL
webhook_url = MIMIC_WEBHOOK_URL

def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def save_text_file(text, filename):
    with open(filename, "w") as file:
        file.write(text)

def parse_events(text):
    pattern = "COMMENT ============================================================================="
    parts = text.split(pattern)
    if len(parts) < 3:
        print("Error: The required data block is not found.")
        return []

    event_text = parts[1].strip()
    event_pattern = re.compile(
        r"COMMENT\s+([\w\s/]+)\s+(\d{3}:\d{2}:\d{2}:\d{2}\.\d{3})\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)")
    matches = event_pattern.findall(event_text)
    if not matches:
        print("No events found.")
        return []

    cleaned_events = []
    for match in matches:
        event_name = match[0].replace("COMMENT", "").strip()
        cleaned_event = {
            "event": event_name,
            "TIG": match[1],
            "DV (M/S)": float(match[2]),
            "HA (KM)": float(match[3]),
            "HP (KM)": float(match[4])
        }
        cleaned_events.append(cleaned_event)
    return cleaned_events

def save_events(events):
    with open("events.json", "w") as file:
        json.dump(events, file)

def load_events():
    try:
        with open("events.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def parse_tig_to_datetime(tig):
    current_year = datetime.utcnow().year
    doy, time_str = tig.split(':')[:1][0], tig.split(':')[1:]
    hour = int(time_str[0])
    minute = int(time_str[1])
    second, millisecond = map(int, time_str[2].split('.'))  # Split seconds and milliseconds

    # Convert day of the year to a date
    doy = int(doy)
    event_date = datetime(current_year, 1, 1) + timedelta(days=doy - 1)
    event_datetime = datetime(
        event_date.year, event_date.month, event_date.day,
        hour, minute, second, millisecond * 1000  # Convert milliseconds to microseconds for datetime
    )
    return event_datetime

def detect_changes(new_events):
    old_events = load_events()
    changed_events = []
    updated_events = []

    for new_event in new_events:
        existing_event = next((event for event in old_events if event["event"] == new_event["event"]), None)
        if existing_event:
            if existing_event["TIG"] != new_event["TIG"]:
                updated_events.append(new_event)
            else:
                changed_events.append(new_event)
        else:
            changed_events.append(new_event)

    if updated_events:
        for updated_event in updated_events:
            for old_event in old_events:
                if old_event["event"] == updated_event["event"]:
                    old_event["TIG"] = updated_event["TIG"]
                    old_event["DV (M/S)"] = updated_event["DV (M/S)"]
                    old_event["HA (KM)"] = updated_event["HA (KM)"]
                    old_event["HP (KM)"] = updated_event["HP (KM)"]
        save_events(old_events)
    else:
        save_events(old_events + changed_events)

    print("Changed events:", changed_events)
    print("Updated events:", updated_events)
    return changed_events, updated_events

def send_discord_message(message):
    global webhook_url
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    response.raise_for_status()

def check_and_send_event_reminders(events):
    now = datetime.utcnow()
    for event in events:
        event_time = parse_tig_to_datetime(event['TIG'])
        if event_time - now <= timedelta(minutes=5) and event_time > now:
            send_discord_message(f"**{event['event']}** is scheduled to occur soon (maybe)")

def schedule_event_checks():
    url = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.txt"
    text_data = download_file(url)
    #save_text_file(text_data, "ISS.OEM_J2K_EPH.txt")  # Save the downloaded text file
    events = parse_events(text_data)
    now = datetime.utcnow()
    changed_events, updated_events = detect_changes(events)

    if changed_events or updated_events:
        message = f"\n**ISS Scheduled Events Detected:** \n"
        for event in changed_events + updated_events:
            event_time = parse_tig_to_datetime(event['TIG'])
            time_delta = event_time - now
            days, seconds = time_delta.days, time_delta.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            time_to_event = f"{days} days, {hours} hours, and {minutes} minutes"
            message += f"\n**{event['event']}** at {event['TIG']} (scheduled in {time_to_event} \n"
        send_discord_message(message)

if __name__ == "__main__":
    schedule.every(1).minutes.do(schedule_event_checks)
    schedule.every(4).minutes.do(check_and_send_event_reminders, load_events())  # Reminder check every minute
    while True:
        schedule.run_pending()
        time.sleep(1)  # Reduce sleep to improve responsiveness
