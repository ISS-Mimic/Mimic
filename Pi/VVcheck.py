import sqlite3
import requests
import urllib.request
from bs4 import BeautifulSoup
import re
import ssl
import pandas as pd
from pathlib import Path

mimic_data_directory = Path.home() / '.mimic_data'

# URL Constants
wikiurl = 'https://en.wikipedia.org/wiki/International_Space_Station'
nasaurl = 'https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/'
vv_db_path = '/dev/shm/vv.db'
output_file = str(mimic_data_directory) + '/vv.png'

def getVV_Image(page_url,output):
    # Fetch the page content
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all image tags
    image_tags = soup.find_all('img')

    # List to hold filtered image URLs
    filtered_image_urls = []

    # Extract all image URLs that match the pattern
    for image_tag in image_tags:
        image_url = image_tag.get('src')
        if not image_url.startswith('http'):
            image_url = 'https://www.nasa.gov' + image_url

        # Filter URLs that match the specific pattern
        if re.search(r'/wp-content/uploads/\d{4}/\d{2}/iss-\d{2}-\d{2}-\d{2}\.png', image_url):
            filtered_image_urls.append(image_url)

    # Select the most recent image URL (assuming the naming convention ensures chronological order)
    if filtered_image_urls:
        target_image_url = sorted(filtered_image_urls)[-1]  # Sort and take the latest one
        context = ssl._create_unverified_context()

        # Download the image using urlopen with the context
        with urllib.request.urlopen(target_image_url, context=context) as response, open(output_file, 'wb') as out_file:
            data = response.read()
            out_file.write(data)

        print(f"Downloaded image from {target_image_url} to {output_file}")
    else:
        print("No matching image URL found.")


# Function to get NASA data
def get_nasa_data(url):
    response = requests.get(nasaurl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        #print(paragraphs)
        nasa_data = []
        date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        for paragraph in paragraphs:
            for event in paragraph:
                if date_pattern.search(event.get_text()):
                    #print(event.get_text())
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

# Get the NASA VV image
getVV_Image(nasaurl,output_file)

# Parse the NASA data
nasa_dock_df, nasa_undock_df = parse_nasa_data(get_nasa_data(nasaurl))


# Function to identify current docked spacecraft
def identify_current_docked(dock_df, undock_df):
    current_docked = dock_df.copy()
    current_docked['Status'] = 'Docked'
    for index, row in undock_df.iterrows():
        event = row['Event'].replace('Undock', 'Dock').replace('Release', 'Capture').replace('Splashdown', 'Dock')
        current_docked = current_docked[~current_docked['Event'].str.contains(event)]
    return current_docked

# Identify current docked spacecraft
current_docked_df = identify_current_docked(nasa_dock_df, nasa_undock_df)

# Function to get Wikipedia data
def get_wikipedia_data(wikiurl):
    tables = pd.read_html(wikiurl)
    df = tables[2]
    return df

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
    df['Arrival (UTC)'] = pd.to_datetime(df['Arrival (UTC)'], errors='coerce')
    df['Departure (planned)'] = df['Departure (planned)'].apply(
        lambda x: convert_net_date(x) if 'NET' in x or 'early' in x or 'mid' in x or 'late' in x
        else pd.to_datetime(x, errors='coerce'))
    return df

# Function to clean citations
def clean_citations(text):
    if isinstance(text, str):
        return re.sub(r'\[\d+\]', '', text)
    else:
        return text

# Obtain the table of current visiting vehicles
wikipedia_df = get_wikipedia_data(wikiurl)

# Remove the citation text that gets added
wikipedia_df = wikipedia_df.applymap(clean_citations)

# Clean the Wikipedia data
wikipedia_df = clean_wikipedia_data(wikipedia_df)

# Function to correlate data
def correlate_data(nasa_df, wiki_df):
    correlated_data = []
    for _, nasa_row in nasa_df.iterrows():
        matching_wiki_rows = wiki_df[wiki_df['Arrival (UTC)'] == nasa_row['Date']]
        for _, wiki_row in matching_wiki_rows.iterrows():
            correlated_data.append({
                'Spacecraft': wiki_row['Spacecraft'],
                'Type': wiki_row['Type'],
                'Mission': wiki_row['Mission'],
                'Event': nasa_row['Event'],
                'Date': nasa_row['Date'],
                'Location': wiki_row['Location'],
                'Arrival': wiki_row['Arrival (UTC)'],
                'Departure': wiki_row['Departure (planned)']
            })
    return pd.DataFrame(correlated_data)

# Correlate the data
correlated_df = correlate_data(current_docked_df, wikipedia_df)

# Function to update SQLite3 database
def update_database(correlated_df, db_path='iss_vehicles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            Spacecraft TEXT,
            Type TEXT,
            Mission TEXT,
            Event TEXT,
            Date DATE,
            Location TEXT,
            Arrival TEXT,
            Departure TEXT
        )
    ''')

    # Remove vehicles that are no longer docked
    cursor.execute('DELETE FROM vehicles')

    # Insert new data
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

    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Update the database with correlated data
update_database(correlated_df,db_path=vv_db_path)

#print(correlated_df)

print("Database updated successfully.")
