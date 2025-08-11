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
from utils.logger import log_info, log_error

pd.set_option('display.max_columns',None)

mimic_data_directory = Path.home() / '.mimic_data'
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

log_info("Running VV Check")


# URL Constants
wikiurl = 'https://en.wikipedia.org/wiki/International_Space_Station'
nasaurl = 'https://www.nasa.gov/international-space-station/space-station-visiting-vehicles/'

# Cross-platform database path handling
import pathlib
#log_info("Setting up cross-platform database paths")

vv_db_path = pathlib.Path('/dev/shm/vv.db')
if not vv_db_path.exists():
    log_info("SHM path not available, using fallback path")
    vv_db_path = pathlib.Path.home() / '.mimic_data' / 'vv.db'
    # Ensure the directory exists
    vv_db_path.parent.mkdir(parents=True, exist_ok=True)
    log_info(f"Created fallback directory: {vv_db_path.parent}")

vv_db_path = str(vv_db_path)
#log_info(f"VV database path: {vv_db_path}")

output_file = str(mimic_data_directory) + '/vv.png'
#log_info(f"Output image path: {output_file}")

# Define a mapping to standardize mission names
mission_name_mapping = {
    'Cygnus CRS-20': 'Cygnus NG-20',
    # Add other mappings as necessary
}


def get_image_hash(image_path):
    """Calculate MD5 hash of an image file."""
    try:
        #log_info(f"Calculating image hash for: {image_path}")
        hasher = hashlib.md5()
        with open(image_path, 'rb') as img_file:
            buf = img_file.read()
            hasher.update(buf)
        hash_value = hasher.hexdigest()
        #log_info(f"Image hash calculated: {hash_value[:8]}...")
        return hash_value
    except FileNotFoundError:
        log_error(f"Image file not found: {image_path}")
        return None
    except Exception as e:
        log_error(f"Error calculating image hash: {e}")
        return None

def getVV_Image(page_url, output):
    """Download and process visiting vehicle image from NASA website."""
    try:
        #log_info(f"Fetching visiting vehicle image from: {page_url}")
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()
        #log_info("Successfully retrieved NASA webpage")

        soup = BeautifulSoup(response.content, 'html.parser')
        image_tags = soup.find_all('img')
        #log_info(f"Found {len(image_tags)} image tags on page")

        filtered_image_urls = []
        for image_tag in image_tags:
            image_url = image_tag.get('src')
            if not image_url.startswith('http'):
                image_url = 'https://www.nasa.gov' + image_url

            # Adjusted regular expression to allow additional characters after the date string
            if re.search(r'/wp-content/uploads/\d{4}/\d{2}/iss-\d{2}-\d{2}-\d{2}(-\d)?\.png', image_url):
                filtered_image_urls.append(image_url)

        #log_info(f"Filtered to {len(filtered_image_urls)} matching ISS images")

        if filtered_image_urls:
            target_image_url = sorted(filtered_image_urls)[-1]
            #log_info(f"Selected target image: {target_image_url}")
            
            context = ssl._create_unverified_context()
            #log_info("Downloading target image")

            with urllib.request.urlopen(target_image_url, context=context) as response:
                new_image_data = response.read()

            new_image_hash = hashlib.md5(new_image_data).hexdigest()
            #log_info(f"Downloaded image hash: {new_image_hash[:8]}...")

            if Path(output).exists():
                current_image_hash = get_image_hash(output)
                if current_image_hash:
                    #log_info(f"Current image hash: {current_image_hash[:8]}...")
                    if new_image_hash == current_image_hash:
                        #log_info("Image has not changed, not downloading.")
                        return False
                    #else:
                        #log_info("Image has changed, will download new version.")
                #else:
                    #log_info("Could not calculate current image hash, will download new version.")
            #else:
                #log_info("No existing image found, will download new version.")

            # Save the new image
            #log_info(f"Saving new image to: {output}")
            with open(output, 'wb') as f:
                f.write(new_image_data)
            #log_info("New image saved successfully")
            return True
        else:
            log_error("No matching image URL found.")
            return False
            
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to retrieve the webpage. Status code: {e}")
        return False
    except Exception as e:
        log_error(f"Error downloading visiting vehicle image: {e}")
        return False

def get_nasa_data(url):
    """Fetch visiting vehicle data from NASA website."""
    try:
        #log_info(f"Fetching NASA visiting vehicle data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        #log_info("Successfully retrieved NASA visiting vehicle data")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        nasa_data = []
        date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        
        #log_info(f"Processing {len(paragraphs)} paragraphs for date patterns")
        
        for paragraph in paragraphs:
            for event in paragraph:
                if isinstance(event, Tag):
                    if date_pattern.search(event.get_text()):
                        nasa_data.append(event.get_text())
        
        #log_info(f"Found {len(nasa_data)} NASA data entries with dates")
        return nasa_data
        
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to retrieve NASA data: {e}")
        return []
    except Exception as e:
        log_error(f"Error fetching NASA data: {e}")
        return []


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
    """Parse NASA visiting vehicle data into dock and undock events."""
    try:
        #log_info(f"Parsing {len(data)} NASA data entries")
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
        
        #log_info(f"Parsed {len(dock_events)} dock events and {len(undock_events)} undock events")
        return dock_df, undock_df
        
    except Exception as e:
        log_error(f"Error parsing NASA data: {e}")
        return pd.DataFrame(), pd.DataFrame()

#log_info("Starting visiting vehicle data processing")

# Download visiting vehicle image
#log_info("Downloading visiting vehicle image")
image_downloaded = getVV_Image(nasaurl, output_file)
if image_downloaded:
    log_info("Visiting vehicle image updated")
else:
    log_info("Visiting vehicle image unchanged or download failed")

# Fetch and parse NASA data
#log_info("Fetching and parsing NASA visiting vehicle data")
nasa_data = get_nasa_data(nasaurl)
if nasa_data:
    nasa_dock_df, nasa_undock_df = parse_nasa_data(nasa_data)
    
    # Apply the mapping to standardize mission names in both DataFrames
    #log_info("Standardizing mission names using mapping")
    nasa_dock_df['Event'] = nasa_dock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))
    nasa_undock_df['Event'] = nasa_undock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))
    
    #log_info("NASA data processing completed successfully")
else:
    log_error("Failed to fetch NASA data, creating empty DataFrames")
    nasa_dock_df, nasa_undock_df = pd.DataFrame(), pd.DataFrame()


def identify_current_docked(dock_df, undock_df):
    current_docked = dock_df.copy()
    current_docked['Status'] = 'Docked'
    for index, row in undock_df.iterrows():
        event = row['Event'].replace('Undock', 'Dock').replace('Release', 'Capture').replace('Splashdown', 'Dock')
        current_docked = current_docked[~current_docked['Event'].str.contains(event)]
    return current_docked


#log_info("Identifying currently docked vehicles")
current_docked_df = identify_current_docked(nasa_dock_df, nasa_undock_df)
#log_info(f"Currently docked vehicles identified: {len(current_docked_df)} vehicles")

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

#log_info("Fetching and processing Wikipedia visiting vehicle data")
wikipedia_df = get_wikipedia_data(wikiurl)
if wikipedia_df is not None:
    #log_info("Successfully retrieved Wikipedia data")
    #log_info("Cleaning citation references from Wikipedia data")
    wikipedia_df = wikipedia_df.map(clean_citations)
    #log_info("Applying location and mission name standardizations")
    wikipedia_df = clean_wikipedia_data(wikipedia_df)
    #log_info("Wikipedia data processing completed successfully")
else:
    log_error("Failed to fetch Wikipedia data, creating empty DataFrame")
    wikipedia_df = pd.DataFrame()


def correlate_data(nasa_df, wiki_df):
    correlated_data = []
    for _, nasa_row in nasa_df.iterrows():
        if pd.isnull(nasa_row['Date']):
            continue
        # Allow a tolerance of +/- 1 day when matching dates
        start_date = nasa_row['Date'] - pd.Timedelta(days=1)
        end_date = nasa_row['Date'] + pd.Timedelta(days=1)
        matching_wiki_rows = wiki_df[wiki_df['Arrival'].between(start_date, end_date)]
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

#log_info("Correlating NASA and Wikipedia data")
correlated_df = correlate_data(current_docked_df, wikipedia_df)
#log_info(f"Correlation completed: {len(correlated_df)} correlated events")

def print_database_events(db_path='iss_vehicles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT Event FROM vehicles')
    rows = cursor.fetchall()
    for row in rows:
        print(row[0])
    conn.close()



def update_database(correlated_df, undock_df, db_path='iss_vehicles.db'):
    """Update the visiting vehicle database with new data."""
    try:
        log_info(f"Updating database at: {db_path}")
        
        # Log DataFrame information for debugging
        if not correlated_df.empty:
            log_info(f"Correlated DataFrame info:")
            log_info(f"  Shape: {correlated_df.shape}")
            log_info(f"  Columns: {list(correlated_df.columns)}")
            log_info(f"  Data types: {correlated_df.dtypes.to_dict()}")
            log_info(f"  Sample data: {correlated_df.head(2).to_dict('records')}")
        
        if not undock_df.empty:
            log_info(f"Undock DataFrame info:")
            log_info(f"  Shape: {undock_df.shape}")
            log_info(f"  Columns: {list(undock_df.columns)}")
            log_info(f"  Data types: {undock_df.dtypes.to_dict()}")
            log_info(f"  Sample data: {undock_df.head(2).to_dict('records')}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        log_info("Creating/updating database table structure")
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
        
        # Clear existing data
        log_info("Clearing existing database records")
        cursor.execute('DELETE FROM vehicles')
        
        # Insert correlated data
        if not correlated_df.empty:
            log_info(f"Inserting {len(correlated_df)} correlated events into database")
            for idx, row in correlated_df.iterrows():
                # Debug logging to see data types
                log_info(f"Processing row {idx}: {dict(row)}")
                
                # Convert pandas types to SQLite-compatible types
                spacecraft = str(row['Spacecraft']) if pd.notna(row['Spacecraft']) else 'Unknown'
                type_val = str(row['Type']) if pd.notna(row['Type']) else 'Unknown'
                mission = str(row['Mission']) if pd.notna(row['Mission']) else 'Unknown'
                event = str(row['Event']) if pd.notna(row['Event']) else 'Unknown'
                date = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Date']) and hasattr(row['Date'], 'strftime') else str(row['Date']) if pd.notna(row['Date']) else 'Unknown'
                location = str(row['Location']) if pd.notna(row['Location']) else 'Unknown'
                arrival = row['Arrival'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Arrival']) and hasattr(row['Arrival'], 'strftime') else str(row['Arrival']) if pd.notna(row['Arrival']) else 'Unknown'
                departure = row['Departure'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Departure']) and hasattr(row['Departure'], 'strftime') else str(row['Departure']) if pd.notna(row['Departure']) else 'Unknown'
                
                log_info(f"Converted values: spacecraft={spacecraft}, type={type_val}, mission={mission}, event={event}, date={date}, location={location}, arrival={arrival}, departure={departure}")
                
                cursor.execute('''
                    INSERT INTO vehicles (Spacecraft, Type, Mission, Event, Date, Location, Arrival, Departure)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (spacecraft, type_val, mission, event, date, location, arrival, departure))
        else:
            log_info("No correlated events to insert")
        
        # Insert undock events
        if not undock_df.empty:
            log_info(f"Inserting {len(undock_df)} undock events into database")
            for idx, row in undock_df.iterrows():
                # Debug logging to see data types
                log_info(f"Processing undock row {idx}: {dict(row)}")
                
                # Convert pandas types to SQLite-compatible types
                event = str(row['Event']) if pd.notna(row['Event']) else 'Unknown'
                date = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Date']) and hasattr(row['Date'], 'strftime') else str(row['Date']) if pd.notna(row['Date']) else 'Unknown'
                
                log_info(f"Converted undock values: event={event}, date={date}")
                
                cursor.execute('''
                    INSERT INTO vehicles (Spacecraft, Type, Mission, Event, Date, Location, Arrival, Departure)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('Unknown', 'Unknown', 'Unknown', event, date, 'Unknown', 'Unknown', 'Unknown'))
        else:
            log_info("No undock events to insert")
        
        conn.commit()
        log_info("Database updated successfully")
        conn.close()
        
    except sqlite3.Error as e:
        log_error(f"SQLite error updating database: {e}")
        if 'conn' in locals():
            conn.close()
        raise
    except Exception as e:
        log_error(f"Error updating database: {e}")
        if 'conn' in locals():
            conn.close()
        raise


def main():
    """Main function to process visiting vehicle data and update database."""
    try:
        log_info("Starting visiting vehicle data processing and database update")
        
        # Update the database
        log_info("Updating visiting vehicle database")
        update_database(correlated_df, nasa_undock_df, db_path=vv_db_path)
        
        log_info("Visiting vehicle processing completed successfully")
        
    except Exception as e:
        log_error(f"Error in main visiting vehicle processing: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"Fatal error in visiting vehicle check: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
else:
    # When imported as a module, just call the main function
    main()
