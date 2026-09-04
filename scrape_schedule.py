import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

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
cal = Calendar()
cal.add('prodid', '-//VC Geldrop Schedule//mxm.dk//')
cal.add('version', '2.0')

print(f"Fetching schedule for {TARGET_TEAM}...")

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
        if TARGET_TEAM in thuis or TARGET_TEAM in gast:
            event_title = f"{thuis} vs {gast}"
            role = "play"
            match_type = "Match"
        elif TARGET_TEAM in scheids:
            event_title = f"{TARGET_TEAM} vs {thuis} & {gast} (Referee)"
            role = "referee"
            match_type = "Match"
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
            
            # Create iCalendar Event
            event = Event()
            event.add('summary', event_title)
            event.add('dtstart', arrival_time)
            event.add('dtend', match_end)
            event.add('location', sporthal)
            event.add('description', f"Match starts at {tijd}\nLocation: {sporthal}\nMatch Type: {match_type}\nRole: {'Playing' if role == 'play' else 'Referee Duty'}")
            
            # Add category to help Spond parse the match type
            event.add('categories', [match_type])
            
            cal.add_component(event)
            print(f"Added event: {event_title} on {date_str} at {tijd}")
            
        except Exception as e:
            print(f"Failed to parse row: {date_str} {tijd} | Error: {e}")

# Write to file
output_file = 'bahman4_schedule.ics'
with open(output_file, 'wb') as f:
    f.write(cal.to_ical())

print(f"Successfully generated {output_file}")
