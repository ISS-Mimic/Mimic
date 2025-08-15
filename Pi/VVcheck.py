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
#log_info("Setting up cross-platform database paths")
vv_db_path = Path('/dev/shm/vv.db')
if not vv_db_path.exists():
    #log_info("SHM path not available, using fallback path")
    vv_db_path = Path.home() / '.mimic_data' / 'vv.db'
    # Ensure the directory exists
    vv_db_path.parent.mkdir(parents=True, exist_ok=True)
    #log_info(f"Created fallback directory: {vv_db_path.parent}")

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
        headers = {
            'User-Agent': 'ISS Mimic Bot (https://github.com/ISS-Mimic; iss.mimic@gmail.com)'
        }
        response = requests.get(page_url, headers=headers, timeout=30)
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


            # Save the new image
            #log_info(f"Saving new image to: {output}")
            with open(output, 'wb') as out_file:
                out_file.write(new_image_data)
            #log_info("New image saved successfully")
            return True
        else:
            log_error("No matching image URL found.")
            return False
            
    except Exception as e:
        log_error(f"Error downloading visiting vehicle image: {e}")
        return False

def get_nasa_data(url):
    """Fetch visiting vehicle data from NASA website."""
    try:
        #log_info(f"Fetching NASA visiting vehicle data from: {url}")
        headers = {
            'User-Agent': 'ISS Mimic Bot (https://github.com/ISS-Mimic; iss.mimic@gmail.com)'
        }
        response = requests.get(url, headers=headers, timeout=30)
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
        ##log_info(f"Parsing {len(data)} NASA data entries")
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
        
        ##log_info(f"Parsed {len(dock_events)} dock events and {len(undock_events)} undock events")
        return dock_df, undock_df
        
    except Exception as e:
        log_error(f"Error parsing NASA data: {e}")
        return pd.DataFrame(), pd.DataFrame()

#log_info("Starting visiting vehicle data processing")

# Download visiting vehicle image
##log_info("Downloading visiting vehicle image")
image_downloaded = getVV_Image(nasaurl, output_file)


# Fetch and parse NASA data
##log_info("Fetching and parsing NASA visiting vehicle data")
nasa_data = get_nasa_data(nasaurl)

if nasa_data:
    nasa_dock_df, nasa_undock_df = parse_nasa_data(nasa_data)
    
    # Apply the mapping to standardize mission names in both DataFrames
    ##log_info("Standardizing mission names using mapping")
    nasa_dock_df['Event'] = nasa_dock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))
    nasa_undock_df['Event'] = nasa_undock_df['Event'].apply(lambda x: standardize_mission_names(x, mission_name_mapping))
    
    ##log_info("NASA data processing completed successfully")
else:
    log_error("Failed to fetch NASA data, creating empty DataFrames")
    nasa_dock_df, nasa_undock_df = pd.DataFrame(), pd.DataFrame()

def identify_current_docked(dock_df, undock_df):
    """Identify currently docked vehicles by removing undock events."""
    try:
        ##log_info("Identifying currently docked vehicles")
        current_docked = dock_df.copy()
        current_docked['Status'] = 'Docked'
        for index, row in undock_df.iterrows():
            event = row['Event'].replace('Undock', 'Dock').replace('Release', 'Capture').replace('Splashdown', 'Dock')
            current_docked = current_docked[~current_docked['Event'].str.contains(event)]
        
        ##log_info(f"Currently docked vehicles identified: {len(current_docked)} vehicles")
        return current_docked
        
    except Exception as e:
        log_error(f"Error identifying currently docked vehicles: {e}")
        return pd.DataFrame()

current_docked_df = identify_current_docked(nasa_dock_df, nasa_undock_df)

def get_wikipedia_data(wikiurl):
    """Fetch visiting vehicle data from Wikipedia."""
    try:
        ##log_info(f"Fetching Wikipedia visiting vehicle data from: {wikiurl}")
        headers = {
            'User-Agent': 'ISS Mimic Bot (https://github.com/ISS-Mimic; iss.mimic@gmail.com)'
        }
        
        # Use requests to get the page content first
        response = requests.get(wikiurl, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse tables from the HTML content
        tables = pd.read_html(response.content)
        ##log_info(f"Found {len(tables)} tables on Wikipedia page")
        
        # Iterate through all tables to find the one with "Arrival" column
        for i, table in enumerate(tables):
            if 'Arrival' in table.columns: # Using "Arrival" as the unique identifier of the table we want (sometimes the table # changes)
                #log_info(f"Found mission table at index {i} with {len(table)} rows")
                return table
        
        log_error("Mission table not found on the Wikipedia page")
        raise ValueError("Mission table not found on the Wikipedia page.")
        
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to retrieve Wikipedia data: {e}")
        raise
    except Exception as e:
        log_error(f"Error fetching Wikipedia data: {e}")
        raise

def convert_net_date(date_str):
    """Convert NET (No Earlier Than) dates to datetime objects."""
    try:
        if 'early' in date_str.lower():
            day = 5
        elif 'mid' in date_str.lower():
            day = 15
        elif 'late' in date_str.lower():
            day = 25
        else:
            day = date_str.split()[-3]
        
        ##log_info(f"Converting NET date: {date_str} -> day {day}")
        
        try:
            return pd.to_datetime(f"{date_str.split()[-1]}-{date_str.split()[-2]}-{day}", format='%Y-%B-%d',
                                  errors='coerce')
        except ValueError:
            ##log_info(f"Fallback conversion for date: {date_str}")
            return pd.to_datetime(f"{date_str.split()[-1]}-{date_str.split()[-2]}-01", format='%Y-%B-%d', errors='coerce')
    except Exception as e:
        log_error(f"Error converting NET date '{date_str}': {e}")
        return pd.NaT

def clean_wikipedia_data(df):
    """Clean and standardize Wikipedia visiting vehicle data."""
    try:
        ##log_info(f"Cleaning Wikipedia data with {len(df)} rows")
        
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
        
        ##log_info("Applying location replacements")
        df['Port'] = df['Port'].replace(location_replacements, regex=True)
        
        ##log_info("Standardizing mission names")
        df['Mission'] = df['Mission'].apply(lambda x: f'Cygnus {x}' if x.startswith('NG-') else x)
        df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Crew-') else x)
        df['Mission'] = df['Mission'].apply(lambda x: f'SpaceX {x}' if x.startswith('Cargo-') else x)
        
        ##log_info("Converting arrival and departure dates")
        df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
        df['Departure'] = df['Departure'].apply(
            lambda x: convert_net_date(x) if 'NET' in x or 'early' in x or 'mid' in x or 'late' in x
            else pd.to_datetime(x, errors='coerce'))
        
        ##log_info("Wikipedia data cleaning completed successfully")
        return df
        
    except Exception as e:
        log_error(f"Error cleaning Wikipedia data: {e}")
        return df

def clean_citations(text):
    if isinstance(text, str):
        # This will remove anything inside square brackets, including [i] and citation references like [1]
        return re.sub(r'\[.*?\]', '', text).strip()
    else:
        return text

# Fetch and process Wikipedia data
##log_info("Fetching Wikipedia visiting vehicle data")
try:
    wikipedia_df = get_wikipedia_data(wikiurl)
    ##log_info(f"Retrieved Wikipedia data with {len(wikipedia_df)} rows")
    
    ##log_info("Cleaning citations from Wikipedia data")
    wikipedia_df = wikipedia_df.applymap(clean_citations)
    
    ##log_info("Cleaning and standardizing Wikipedia data")
    wikipedia_df = clean_wikipedia_data(wikipedia_df)
    
    ##log_info("Wikipedia data processing completed successfully")
    
except Exception as e:
    log_error(f"Failed to process Wikipedia data: {e}")
    wikipedia_df = pd.DataFrame()

def correlate_data(nasa_df, wiki_df):
    """Correlate NASA and Wikipedia visiting vehicle data."""
    try:
        ##log_info("Correlating NASA and Wikipedia data")
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
        
        ##log_info(f"Correlated {len(correlated_data)} data entries")
        return pd.DataFrame(correlated_data)
        
    except Exception as e:
        log_error(f"Error correlating data: {e}")
        return pd.DataFrame()


# Correlate NASA and Wikipedia data
##log_info("Starting data correlation")
correlated_df = correlate_data(current_docked_df, wikipedia_df)
##log_info(f"Data correlation completed: {len(correlated_df)} correlated entries")

def print_database_events(db_path='iss_vehicles.db'):
    """Print all events from the vehicles database."""
    try:
        ##log_info(f"Printing database events from: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT Event FROM vehicles')
        rows = cursor.fetchall()
        ##log_info(f"Found {len(rows)} events in database")
        #for row in rows:
            #log_info(f"Event: {row[0]}")
        conn.close()
    except Exception as e:
        log_error(f"Error printing database events: {e}")

#print("Existing events in the database:")
#print_database_events(db_path=vv_db_path)

def update_database(correlated_df, undock_df, db_path='iss_vehicles.db'):
    """Update the visiting vehicle database with new data."""
    try:
        ##log_info(f"Updating database at: {db_path}")
        ##log_info(f"Correlated data: {len(correlated_df)} entries")
        ##log_info(f"Undock data: {len(undock_df)} entries")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        ##log_info("Creating vehicles table if it doesn't exist")
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
        ##log_info("Clearing existing vehicle data")
        cursor.execute('DELETE FROM vehicles')
        ##log_info(f"Cleared {cursor.rowcount} existing records")

        # Remove vehicles that are no longer docked based on the undock events
        ##log_info("Processing undock events to remove departed vehicles")
        for _, row in undock_df.iterrows():
            event = row['Event']
            ##log_info(f"Removing vehicles with event: {event}")
            cursor.execute('DELETE FROM vehicles WHERE Event LIKE ?', ('%' + event + '%',))
            ##log_info(f"Removed {cursor.rowcount} records for event: {event}")

        # Insert new data
        ##log_info("Inserting new correlated vehicle data")
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

        ##log_info(f"Inserted {len(correlated_df)} new vehicle records")
        
        conn.commit()
        conn.close()
        #log_info("Database update completed successfully")
        
    except Exception as e:
        log_error(f"Error updating database: {e}")
        if 'conn' in locals():
            conn.close()


# Update the database with new data
#log_info("Starting database update process")
try:
    update_database(correlated_df, nasa_undock_df, db_path=vv_db_path)
    #log_info("Database update process completed successfully")
except Exception as e:
    log_error(f"Database update process failed: {e}")


# Function to verify and display data from the database
def verify_database(db_path='iss_vehicles.db'):
    """Verify and display data from the vehicles database."""
    try:
        #log_info(f"Verifying database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query to select all data from the vehicles table
        cursor.execute('SELECT * FROM vehicles')
        rows = cursor.fetchall()


        # Close the connection
        conn.close()
        
    except Exception as e:
        log_error(f"Error verifying database: {e}")


# Call the function to verify data (uncomment for debugging)
#verify_database(db_path=vv_db_path)


def main():
    """Main function to run the visiting vehicle check process."""
    try:
        log_info("Starting VVcheck.py main execution")
        
        # All the processing logic is already executed at module level
        # This function provides a clean entry point if needed

        
    except Exception as e:
        log_error(f"VVcheck.py main execution failed: {e}")
        raise

if __name__ == "__main__":
    main()