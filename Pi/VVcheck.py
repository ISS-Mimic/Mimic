import sqlite3
import requests
import urllib.request
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import ssl
import pandas as pd
from pathlib import Path
import os.path as op #use for getting mimic directory
import hashlib
import logging
from logging.handlers import RotatingFileHandler

pd.set_option('display.max_columns',None)

mimic_data_directory = Path.home() / '.mimic_data'
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

# Set up basic configuration for the logging system
log_file_path = mimic_directory + '/Mimic/Pi/Logs/mimiclog_vvcheck.log'

logger = logging.getLogger('MyLogger')
logger.setLevel(logging.ERROR)  # Set logger to INFO level

# Create handler
handler = RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
handler.setLevel(logging.ERROR)  # Set handler to INFO level

# Add handler to logger
if not logger.hasHandlers():
    logger.addHandler(handler)

logger.info("Running VV Check")

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)


# URL Constants
wikiurl = 'https://en.wikipedia.org/wiki/International_Space_Station'
nasaurl = 'https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/'
vv_db_path = '/dev/shm/vv.db'
output_file = str(mimic_data_directory) + '/vv.png'

# Define a mapping to standardize mission names
mission_name_mapping = {
    'Cygnus CRS-20': 'Cygnus NG-20',
    # Add other mappings as necessary
}


def get_image_hash(image_path):
    hasher = hashlib.md5()
    with open(image_path, 'rb') as img_file:
        buf = img_file.read()
        hasher.update(buf)
    return hasher.hexdigest()

def getVV_Image(page_url, output):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    image_tags = soup.find_all('img')
    filtered_image_urls = []

    for image_tag in image_tags:
        image_url = image_tag.get('src')
        if not image_url.startswith('http'):
            image_url = 'https://www.nasa.gov' + image_url

        # Adjusted regular expression to allow additional characters after the date string
        if re.search(r'/wp-content/uploads/\d{4}/\d{2}/iss-\d{2}-\d{2}-\d{2}(-\d)?\.png', image_url):
            filtered_image_urls.append(image_url)

    if filtered_image_urls:
        target_image_url = sorted(filtered_image_urls)[-1]
        context = ssl._create_unverified_context()

        with urllib.request.urlopen(target_image_url, context=context) as response:
            new_image_data = response.read()

        new_image_hash = hashlib.md5(new_image_data).hexdigest()

        if Path(output).exists():
            current_image_hash = get_image_hash(output)
        else:
            current_image_hash = None

        if new_image_hash != current_image_hash:
            with open(output, 'wb') as out_file:
                out_file.write(new_image_data)
            log_info(f"Downloaded image from {target_image_url} to {output}")
        else:
            log_info("Image has not changed, not downloading.")
    else:
        log_error("No matching image URL found.")

def get_nasa_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        nasa_data = []
        date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        
        for paragraph in paragraphs:
            for event in paragraph:
                if isinstance(event, Tag):
                    if date_pattern.search(event.get_text()):
                        nasa_data.append(event.get_text())
    else:
        log_error(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    
    return nasa_data


def standardize_date(date_str):
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except:
        date_str = re.sub(r'(\d{1,2}/\d{1,2}/)(\d{2})$', r'\g<1>20\2', date_str)
        return pd.to_datetime(date_str, errors='coerce')

def standardize_mission_names(event, mapping):
    for key, value in mapping.items():
        event = event.replace(key, value)
    return event


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
    #print("---NASA DFs---")
    #print(dock_df)
    #print(undock_df)
    return dock_df, undock_df

getVV_Image(nasaurl, output_file)
nasa_dock_df, nasa_undock_df = parse_nasa_data(get_nasa_data(nasaurl))

# Apply the mapping to standardize mission names in both DataFrames
nasa_dock_df['Event'] = nasa_dock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))
nasa_undock_df['Event'] = nasa_undock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))

def identify_current_docked(dock_df, undock_df):
    current_docked = dock_df.copy()
    current_docked['Status'] = 'Docked'
    for index, row in undock_df.iterrows():
        event = row['Event'].replace('Undock', 'Dock').replace('Release', 'Capture').replace('Splashdown', 'Dock')
        current_docked = current_docked[~current_docked['Event'].str.contains(event)]
    return current_docked

current_docked_df = identify_current_docked(nasa_dock_df, nasa_undock_df)

def get_wikipedia_data(wikiurl):
    tables = pd.read_html(wikiurl)
    
    # Iterate through all tables to find the one with "Arrival" column
    for table in tables:
        if 'Arrival' in table.columns: # Using "Arrival" as the unique identifier of the table we want (sometimes the table # changes)
            #print(table)
            return table
    
    raise ValueError("Mission table not found on the Wikipedia page.")

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

def clean_wikipedia_data(df):
    location_replacements = {
        'Harmony': 'Node 2',
        'Poisk': 'MRM-2',
        'Rassvet': 'MRM-1',
        'Prichal': 'RS Node',
        'Zvezda': 'Service Module',
        'Unity': 'Node 1',
        'Zarya': 'FGB',
        'forward': 'Forward',
        'aft': 'Aft',
        'zenith': 'Zenith',
        'nadir': 'Nadir',
    }
    df['Port'] = df['Port'].replace(location_replacements, regex=True)
    df['Mission'] = df['Mission'].apply(lambda x: f'Cygnus {x}' if x.startswith('NG-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Crew-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Cargo-') else x)
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Departure'] = df['Departure'].apply(
        lambda x: convert_net_date(x) if 'NET' in x or 'early' in x or 'mid' in x or 'late' in x
        else pd.to_datetime(x, errors='coerce'))
    return df

def clean_citations(text):
    if isinstance(text, str):
        # This will remove anything inside square brackets, including [i] and citation references like [1]
        return re.sub(r'\[.*?\]', '', text).strip()
    else:
        return text

wikipedia_df = get_wikipedia_data(wikiurl)
#print(wikipedia_df)
wikipedia_df = wikipedia_df.applymap(clean_citations)
#print(wikipedia_df)
wikipedia_df = clean_wikipedia_data(wikipedia_df)
#print(wikipedia_df)

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
                'Location': wiki_row['Port'],
                'Arrival': wiki_row['Arrival'],
                'Departure': wiki_row['Departure']
            })
    return pd.DataFrame(correlated_data)

correlated_df = correlate_data(current_docked_df, wikipedia_df)
#print(correlated_df)

def print_database_events(db_path='iss_vehicles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT Event FROM vehicles')
    rows = cursor.fetchall()
    for row in rows:
        print(row[0])
    conn.close()

#print("Existing events in the database:")
#print_database_events(db_path=vv_db_path)

def update_database(correlated_df, undock_df, db_path='iss_vehicles.db'):
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

    # Clear the database first
    cursor.execute('DELETE FROM vehicles')

    # Print existing events before deletion for debugging
    #print("Existing events in the database before deletion:")
    #cursor.execute('SELECT Event FROM vehicles')
    #rows = cursor.fetchall()
    #for row in rows:
    #    print(row[0])

    # Remove vehicles that are no longer docked based on the undock events
    for _, row in undock_df.iterrows():
        event = row['Event']
        #print(f"Attempting to remove event: {event}")
        cursor.execute('DELETE FROM vehicles WHERE Event LIKE ?', ('%' + event + '%',))
        #print(f"Rows affected: {cursor.rowcount}")

    # Insert new data
    for _, row in correlated_df.iterrows():
        #print(row['Port'])
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

    
    conn.commit()
    conn.close()


update_database(correlated_df, nasa_undock_df, db_path=vv_db_path)


# Function to verify and display data from the database
def verify_database(db_path='iss_vehicles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to select all data from the vehicles table
    cursor.execute('SELECT * FROM vehicles')

    # Fetch all results
    rows = cursor.fetchall()

    # Check if there are any results
    if rows:
        # Print the results
        for row in rows:
            print(row)
    else:
        print("No data found in the database.")

    # Close the connection
    conn.close()

# Call the function to verify data
#verify_database(db_path=vv_db_path)


log_info("Database updated successfully.")
