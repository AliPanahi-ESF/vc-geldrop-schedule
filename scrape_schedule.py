import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import csv

# Target team name (Ensure this matches the website exactly)
TARGET_TEAM = "Bahman 4"

# All available poules in the VC Geldrop system
POULES = ["HK", "OK", "TK", "1", "2", "3", "4"]
BASE_URL = "https://vc-geldrop.nl/cgi-bin/volley_results.pl"

# Month mapping for Dutch abbreviations
MONTHS = {
    'jan': 1, 'feb': 2, 'mrt': 3, 'apr': 4, 'mei': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
}

tz = pytz.timezone('Europe/Amsterdam')

print(f"Fetching schedule for {TARGET_TEAM}...")

events = []

for poule in POULES:
    response = requests.get(BASE_URL, params={'entry': 'speeldata', 'poule': poule})
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', id='VCGeldrop')
    if not table:
        continue
        
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) < 7:
            continue
            
        # 1. Extract Date and Time
        datum_text = cols[0].get_text(separator=' ', strip=True) 
        parts = datum_text.split()
        if not parts: 
            continue
        date_str = parts[-1] # Expected format: "22-sep-'26"
        tijd = cols[1].get_text(strip=True) # Expected format: "21:00"
        
        # 2. Extract Teams and Roles
        thuis = cols[2].get_text(strip=True)
        gast = cols[3].get_text(strip=True)
        scheids = cols[4].get_text(strip=True)
        
        # 3. Extract Location
        sporthal = cols[5].get_text(separator=', ', strip=True).replace(', ,', ',')
        
        # Determine event type
        if TARGET_TEAM in thuis:
            match_type = "Home"
        elif TARGET_TEAM in gast:
            match_type = "Away"
        elif TARGET_TEAM in scheids:
            match_type = "Referee" # fallback to their spelling if needed, but 'Referee' is standard
        else:
            continue
            
        try:
            # Parse Date elements
            day, month_nl, year_short = date_str.split('-')
            year = int(year_short.replace("'", "")) + 2000
            month = MONTHS[month_nl.lower()]
            day = int(day)
            hour, minute = map(int, tijd.split(':'))
            
            # Construct timezone-aware datetime objects
            match_start = tz.localize(datetime(year, month, day, hour, minute))
            
            # Arrival time (30 mins before match) and End time (assume 2 hours duration)
            arrival_time = match_start - timedelta(minutes=30)
            match_end = match_start + timedelta(hours=2)
            
            # Format dates and times for the CSV
            start_date_str = match_start.strftime("%d/%m/%Y")
            start_time_str = match_start.strftime("%H:%M")
            meet_up_str = arrival_time.strftime("%H:%M")
            end_date_str = match_end.strftime("%d/%m/%Y")
            end_time_str = match_end.strftime("%H:%M")
            
            # Simple description
            desc = "Referee Duty" if match_type == "Referee" else "League Match"
            
            events.append({
                "Start date*": start_date_str,
                "Start time": start_time_str,
                "Meet up": meet_up_str,
                "End date": end_date_str,
                "End time": end_time_str,
                "Match Type*": match_type,
                "Home Team*": thuis,
                "Away Team*": gast,
                "Description": desc,
                "Place": sporthal
            })
            
            print(f"Added event: {thuis} vs {gast} on {start_date_str} at {start_time_str}")
            
        except Exception as e:
            print(f"Failed to parse row: {date_str} {tijd} | Error: {e}")

# Write to CSV file
output_file = 'bahman4_schedule.csv'
headers = [
    "Start date*", "Start time", "Meet up", "End date", "End time",
    "Match Type*", "Home Team*", "Away Team*", "Description", "Place"
]

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for e in events:
        writer.writerow(e)

print(f"Successfully generated {output_file}")
