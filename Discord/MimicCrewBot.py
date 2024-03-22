import re
import requests
import time
import json
import os
from datetime import datetime, timedelta
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL

def get_iss_crew_info():
    print("getting ISS crew")
    url = "https://en.wikipedia.org/w/api.php?action=parse&page=Template:People_currently_in_space&prop=wikitext&format=json"
    response = requests.get(url)
    data = response.json()

    template_content = data['parse']['wikitext']['*']
    iss_match = re.search(r'International Space Station.*?(?=Tiangong space station)', template_content, re.DOTALL)

    if not iss_match:
        return []

    iss_section = iss_match.group(0)
    spaceships = re.findall(r'\[\[([^\]]+)\]\]', iss_section)
    countries = re.findall(r'size=15px\|([^}]+)', iss_section)

    crew_info = []
    current_ship = ''
    expedition = ''
    idx = 0

    for spaceship in spaceships:
        if "Expedition" in spaceship:
            expedition = spaceship
            continue
        if "SpaceX" in spaceship or "Soyuz" in spaceship or "Axiom" in spaceship or "Boeing" in spaceship:
            current_ship = spaceship
            continue
        else:
            crew_info.append(
                {'name': spaceship, 'spaceship': current_ship, 'country': countries[idx], 'expedition': expedition})
            idx += 1

    return crew_info


def format_message(crew_info_list):
    """Format the entire message based on the crew information."""
    # Extract the expedition info, which is common for all crew members
    expedition = crew_info_list[0]['expedition'] if crew_info_list else "Unknown"

    message = f"ISS Crew Change detected! \n\nThe current ISS expedition is **{expedition}**.\n\nThe currently docked crew spacecraft are:\n"

    # Group crew members by their spacecraft
    spacecraft_group = {}
    for member in crew_info_list:
        if member['spaceship'] not in spacecraft_group:
            spacecraft_group[member['spaceship']] = []
        # Combine the member name with their country in parentheses
        member_info = f"{member['name']} ({member['country']})"
        spacecraft_group[member['spaceship']].append(member_info)

    index = 0

    # Format the spacecraft and their crew members
    for spacecraft, members in spacecraft_group.items():
        # Insert "and" before the last member's name if there are multiple members
        if len(members) > 1:
            last_member = members.pop()
            member_list = ", ".join(members) + f", and {last_member}"
        else:
            member_list = members[0]
        message += f"\n**{spacecraft}** with: {member_list}."
        if index == 0:
            message += f"\n"
            message += f"\n and \n"
            index += 1

    return message

def send_discord_message(crew_info_list):
    global discord_webhook_url
    """Send the crew information as a single message."""
    formatted_info = format_message(crew_info_list)
    data = {'content': formatted_info}
    response = requests.post(discord_webhook_url, json=data)
    return response.status_code

def main():
    global discord_webhook_url
    
    #discord_webhook_url = TEST_WEBHOOK_URL
    discord_webhook_url = MIMIC_WEBHOOK_URL
    
    # Load previous data if exists
    if os.path.exists('previous_data.json'):
        with open('previous_data.json', 'r') as f:
            previous_data = json.load(f)
    else:
        previous_data = []

    # Fetch current data
    current_data = get_iss_crew_info()
    # Compare and send message if changed
    if current_data != previous_data:
        #send_discord_message(f"Crew data has changed! The current ISS crew is:\n\n{current_data}")
        send_discord_message(current_data)
        with open('previous_data.json', 'w') as f:
            json.dump(current_data, f)

    # Wait for an hour and then check again
    next_check_time = datetime.now() + timedelta(hours=1)

    while True:
        if datetime.now() >= next_check_time:
            print("running")
            main()

if __name__ == "__main__":
    main()

