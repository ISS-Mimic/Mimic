import sqlite3
import requests
import urllib.request
from bs4 import BeautifulSoup
import re
import ssl
import pandas as pd
from config import TEST_WEBHOOK_URL, MIMIC_WEBHOOK_URL
from pathlib import Path
import time

# URL Constants
wikiurl = 'https://en.wikipedia.org/wiki/International_Space_Station'
nasaurl = 'https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/'
vv_db_path = 'vv.db'
output_file = 'vv.png'
#webhook_url = TEST_WEBHOOK_URL
webhook_url = MIMIC_WEBHOOK_URL

# Define a mapping to standardize mission names
mission_name_mapping = {
    'Cygnus CRS': 'Cygnus NG',
    # Add other mappings as necessary
}

# Function to send a Discord message
def send_discord_message(webhook_url, message, file_path=None):
    data = {"content": message}
    files = {"file": open(file_path, "rb")} if file_path else None
    response = requests.post(webhook_url, data=data, files=files)
    if response.status_code in (200, 204):
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}, response: {response.text}")

# Function to get the latest NASA VV image
def getVV_Image(page_url, output):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    image_tags = soup.find_all('img')
    filtered_image_urls = []

    for image_tag in image_tags:
        image_url = image_tag.get('src')
        if not image_url.startswith('http'):
            image_url = 'https://www.nasa.gov' + image_url

        if re.search(r'/wp-content/uploads/\d{4}/\d{2}/iss-\d{2}-\d{2}-\d{2}\.png', image_url):
            filtered_image_urls.append(image_url)

    if filtered_image_urls:
        target_image_url = sorted(filtered_image_urls)[-1]
        context = ssl._create_unverified_context()

        # Check if the current image is newer than the last one
        last_downloaded_file = "last_downloaded.txt"
        last_downloaded = ""

        if Path(last_downloaded_file).exists():
            with open(last_downloaded_file, "r") as f:
                last_downloaded = f.read().strip()

        if last_downloaded != target_image_url:
            # Download the new image
            with urllib.request.urlopen(target_image_url, context=context) as response, open(output, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            with open(last_downloaded_file, "w") as f:
                f.write(target_image_url)

            send_discord_message(webhook_url, "New NASA Visiting Vehicle image available:", output)
    else:
        print("No matching image URL found.")

# Function to get NASA data
def get_nasa_data(url):
    response = requests.get(nasaurl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        nasa_data = []
        date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        for paragraph in paragraphs:
            for event in paragraph:
                if date_pattern.search(event.get_text()):
                    nasa_data.append(event.get_text())
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    return nasa_data

# Function to standardize dates
def standardize_date(date_str):
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except:
        date_str = re.sub(r'(\d{1,2}/\d{1,2}/)(\d{2})$', r'\g<1>20\2', date_str)
        return pd.to_datetime(date_str, errors='coerce')

# Function to standardize mission names
def standardize_mission_names(event, mapping):
    for key, value in mapping.items():
        event = event.replace(key, value)
    return event

# Function to parse NASA data
def parse_nasa_data(data):
    dock_events = []
    undock_events = []
    for line in data:
        match = re.search(r'(\b\d{1,2}/\d{1,2}/\d{2,4}\b)\s*[\u002D\u2013\u2014]\s*(.*)', line)
        if match:
            date = match.group(1)
            event = match.group(2)
            if any(keyword in event for keyword in ['Dock', 'Capture']):
                dock_events.append({'Date': standardize_date(date.strip()), 'Event': event.strip()})
            elif any(keyword in event for keyword in ['Undock', 'Release', 'Splashdown']):
                undock_events.append({'Date': standardize_date(date.strip()), 'Event': event.strip()})
    dock_df = pd.DataFrame(dock_events)
    undock_df = pd.DataFrame(undock_events)
    return dock_df, undock_df

# Function to identify current docked spacecraft
def identify_current_docked(dock_df, undock_df):
    current_docked = dock_df.copy()
    current_docked['Status'] = 'Docked'
    for index, row in undock_df.iterrows():
        event = row['Event'].replace('Undock', 'Dock').replace('Release', 'Capture').replace('Splashdown', 'Dock')
        current_docked = current_docked[~current_docked['Event'].str.contains(event)]
    return current_docked


def get_wikipedia_data(wikiurl):
    tables = pd.read_html(wikiurl)

    # Iterate through all tables to find the one with "Arrival" column
    for table in tables:
        if 'Arrival' in table.columns: # Using "Arrival" as the unique identifier of the table we want (sometimes the table # changes)
            return table

    raise ValueError("Mission table not found on the Wikipedia page.")


# Function to convert 'NET' dates to approximate dates
def convert_net_date(date_str):
    if 'early' in date_str.lower():
        day = 5
    elif 'mid' in date_str.lower():
        day = 15
    elif 'late' in date_str.lower():
        day = 25
    else:
        day = date_str.split()[-3]
    try:
        return pd.to_datetime(f"{date_str.split()[-1]}-{date_str.split()[-2]}-{day}", format='%Y-%B-%d',
                              errors='coerce')
    except ValueError:
        return pd.to_datetime(f"{date_str.split()[-1]}-{date_str.split()[-2]}-01", format='%Y-%B-%d', errors='coerce')

# Function to clean Wikipedia data
def clean_wikipedia_data(df):
    location_replacements = {
        'Harmony': 'Node 2',
        'Poisk': 'MRM-2',
        'Prichal': 'RS Node',
        'Zvezda': 'Service Module',
        'Unity': 'Node 1',
        'Zarya': 'FGB',
        'forward': 'Forward',
        'aft': 'Aft',
        'zenith': 'Zenith',
        'nadir': 'Nadir',
    }
    df['Location'] = df['Location'].replace(location_replacements, regex=True)
    df['Mission'] = df['Mission'].apply(lambda x: f'Cygnus {x}' if x.startswith('NG-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Crew-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Cargo-') else x)
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Departure'] = df['Departure'].apply(
        lambda x: convert_net_date(x) if 'NET' in x or 'early' in x or 'mid' in x or 'late' in x
        else pd.to_datetime(x, errors='coerce'))
    return df

# Function to clean citations
def clean_citations(text):
    if isinstance(text, str):
        return re.sub(r'\[\d+\]', '', text)
    else:
        return text

# Function to correlate NASA and Wikipedia data
def correlate_data(nasa_df, wiki_df):
    correlated_data = []
    for _, nasa_row in nasa_df.iterrows():
        matching_wiki_rows = wiki_df[wiki_df['Arrival'] == nasa_row['Date']]
        for _, wiki_row in matching_wiki_rows.iterrows():
            correlated_data.append({
                'Spacecraft': wiki_row['Spacecraft'],
                'Type': wiki_row['Type'],
                'Mission': wiki_row['Mission'],
                'Event': nasa_row['Event'],
                'Date': nasa_row['Date'],
                'Location': wiki_row['Location'],
                'Arrival': wiki_row['Arrival'],
                'Departure': wiki_row['Departure']
            })
    return pd.DataFrame(correlated_data)

# Function to update the database and send Discord messages
def update_database(correlated_df, undock_df, db_path='iss_vehicles.db', webhook_url=''):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            Spacecraft TEXT,
            Type TEXT,
            Mission TEXT,
            Event TEXT,
            Date TEXT,
            Location TEXT,
            Arrival TEXT,
            Departure TEXT
        )
    ''')

    # Track existing vehicles before update
    cursor.execute('SELECT Spacecraft, Mission, Location FROM vehicles')
    existing_vehicles = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    # Clear the database first
    cursor.execute('DELETE FROM vehicles')

    # Insert new data
    new_vehicles = {}
    for _, row in correlated_df.iterrows():
        cursor.execute('''
            INSERT INTO vehicles (Spacecraft, Type, Mission, Event, Date, Location, Arrival, Departure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['Spacecraft'],
            row['Type'],
            row['Mission'],
            row['Event'],
            row['Date'].strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row['Date']) else None,
            row['Location'],
            row['Arrival'].strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row['Arrival']) else None,
            row['Departure'].strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row['Departure']) else None
        ))
        new_vehicles[row['Spacecraft']] = (row['Mission'], row['Location'])

    conn.commit()
    conn.close()

    # Determine which vehicles have arrived and left
    arrived_vehicles = new_vehicles.keys() - existing_vehicles.keys()
    departed_vehicles = existing_vehicles.keys() - new_vehicles.keys()

    # Send Discord messages for arrivals and departures
    for vehicle in arrived_vehicles:
        mission, location = new_vehicles[vehicle]
        send_discord_message(webhook_url, f"**A vehicle has docked/berthed to the ISS:**\n"
                                          f"**Vehicle**: {vehicle}\n"
                                          f"**Mission**: {mission}\n"
                                          f"**Location**: {location}\n\n")

    for vehicle in departed_vehicles:
        mission, location = existing_vehicles[vehicle]
        send_discord_message(webhook_url, f"**A vehicle has departed from the ISS:**\n"
                                          f"**Vehicle**: {vehicle}\n"
                                          f"**Mission**: {mission}\n"
                                          f"**Location**: {location}\n\n")

# Function to verify and display data from the database
def verify_database(db_path='iss_vehicles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM vehicles')
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            print(row)
    else:
        print("No data found in the database.")

    conn.close()

# Main loop to periodically check for updates
while True:
    try:
        # Get and process NASA data
        getVV_Image(nasaurl, output_file)
        nasa_data = get_nasa_data(nasaurl)
        nasa_dock_df, nasa_undock_df = parse_nasa_data(nasa_data)
        #print(nasa_dock_df)

        # Get and process Wikipedia data
        wikipedia_df = get_wikipedia_data(wikiurl)
        #print("----------------------------------------")
        #print(wikipedia_df)
        wikipedia_df = wikipedia_df.applymap(clean_citations)
        #print("----------------------------------------")
        #print(wikipedia_df)
        wikipedia_df = clean_wikipedia_data(wikipedia_df)
        #print("----------------------------------------")
        #print(wikipedia_df)

        # Correlate data
        current_docked_df = identify_current_docked(nasa_dock_df, nasa_undock_df)
        correlated_df = correlate_data(current_docked_df, wikipedia_df)

        # Update database and send Discord messages
        update_database(correlated_df, nasa_undock_df, db_path=vv_db_path, webhook_url=webhook_url)

        # Verify database contents
        # verify_database(db_path=vv_db_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        #print(correlated_df['Location'])

    # Sleep for 5 minutes before checking again
    time.sleep(300)
