import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

wikiurl = 'https://en.wikipedia.org/wiki/International_Space_Station'
nasaurl = 'https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/'


def get_nasa_data(url):
    # Send a GET request to the URL
    response = requests.get(nasaurl)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all paragraph tags
        paragraphs = soup.find_all('p')
        nasa_data = []

        # Regular expression to detect dates in m/d/yy or m/d/yyyy format
        date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')

        # Extract text from each paragraph
        for paragraph in paragraphs:
            for event in paragraph:
                if date_pattern.search(event.get_text()):
                    nasa_data.append(event.get_text())

    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

    # print(nasa_data)

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
        # Use regex to extract date and event
        match = re.search(r'(\b\d{1,2}/\d{1,2}/\d{2,4}\b)\s*–\s*(.*)', line)
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


# Parse the NASA data
nasa_dock_df, nasa_undock_df = parse_nasa_data(get_nasa_data(nasaurl))

#print(nasa_dock_df)


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


#print(current_docked_df)


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


# Function to standardize date formats and clean data
def clean_wikipedia_data(df):
    # Standardize location names
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

    # Replace mission names in the 'Mission' column
    df['Mission'] = df['Mission'].apply(lambda x: f'Cygnus {x}' if x.startswith('NG-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Crew-') else x)
    df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Cargo-') else x)

    # Convert date columns to datetime
    df['Arrival (UTC)'] = pd.to_datetime(df['Arrival (UTC)'], errors='coerce')
    df['Departure (planned)'] = df['Departure (planned)'].apply(
        lambda x: convert_net_date(x) if 'NET' in x or 'early' in x or 'mid' in x or 'late' in x
        else pd.to_datetime(x, errors='coerce'))
    return df


# Function to clean up citations
def clean_citations(text):
    if isinstance(text, str):  # Check if text is a string
        return re.sub(r'\[\d+\]', '', text)  # Remove citations
    else:
        return text  # Return non-string values as-is


# Obtain the table of current visiting vehicles
wikipedia_df = get_wikipedia_data(wikiurl)

# Remove the citation text that gets added
wikipedia_df = wikipedia_df.map(clean_citations)

# Rename stuff from the Wikipedia data
wikipedia_df = clean_wikipedia_data(wikipedia_df)


# print(wikipedia_df["Departure (planned)"])

# Assuming you have the NASA data already parsed, correlate the data
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


# Assuming you have the NASA data already in 'current_docked_df'
correlated_df = correlate_data(current_docked_df, wikipedia_df)

# Display the correlated data with altered names
print("Correlated Data:")
print(correlated_df["Mission"])
print(correlated_df["Type"])
print(correlated_df["Location"])
print(correlated_df["Arrival"])
print(correlated_df["Departure"])
