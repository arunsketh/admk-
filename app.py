import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# --- Streamlit Page Setup ---
st.set_page_config(page_title="TN Alliance Map", layout="wide")
st.title("Tamil Nadu Election: Spatial Constituency Map")
st.markdown("Interactive map showing the distribution of seats among alliance parties and ADMK.")

# --- Data Definition ---
alliance_constituencies = {
    'BJP': [
        'Mylapore', 'Thalli', 'Modakkurichi', 'Udhagamandalam', 'Avinashi', 
        'Tiruppur South', 'Coimbatore North', 'Gandharvakottai', 'Pudukkottai', 
        'Tiruppattur', 'Madurai South', 'Sattur', 'Tiruchendur', 'Vasudevanallur', 
        'Radhapuram', 'Nagercoil', 'Vilavancode', 'Avadi', 'Tiruvannamalai', 
        'Thanjavur', 'Tiruvarur', 'Aranthangi', 'Manamadurai', 'Ramanathapuram', 
        'Colachel', 'Padmanabhapuram', 'Rasipuram'
    ],
    'PMK': [
        'Salem West', 'Salem North', 'Dharmapuri', 'Pennagaram', 'Vikravandi', 
        'Sholingur', 'Thiruporur', 'Uthiramerur', 'Jayankondam', 'Vridhachalam', 
        'Mayiladuthurai', 'Gingee', 'Polur', 'Kilvelur', 'Rishivandiyam', 
        'Kattumannarkoil', 'Perambur', 'Ambattur'
    ],
    'AMMK': [
        'Periyakulam', 'Mannargudi', 'Thiruvaiyaru', 'Karaikudi', 'Tiruppattur', 
        'Nanguneri', 'Ottapidaram', 'Trichy West', 'Saidapet', 'Poonamallee', 
        'Madathukulam'
    ],
    'TMC': ['Oddanchatram', 'Erode West', 'Ranipet', 'Killiyur', 'Kumbakonam'],
    'IJK': ['Pallavaram', 'Kunnam'],
    'TMMK': ['Rajapalayam'],
    'Puratchi Bharatham': ['K.V. Kuppam']
}

# Master list of all 234 TN Constituencies. 
# (Add any remaining constituency names here to have them automatically assigned to ADMK)
all_tn_constituencies = [
    'Edappadi', 'Bodinayakanur', 'Royapuram', 'Thondamuthur', 'Gobichettipalayam',
    'Viralimalai', 'Kinathukadavu', 'Thirumangalam', 'Sivakasi', 'Karur'
] 
# Add the alliance ones to the master list so the math works
for seats in alliance_constituencies.values():
    all_tn_constituencies.extend(seats)

# Automatically assign the "unlisted" constituencies to ADMK
all_listed = [seat for seats in alliance_constituencies.values() for seat in seats]
admk_seats = [seat for seat in set(all_tn_constituencies) if seat not in all_listed]

# Final dictionary with ADMK included
all_constituencies = alliance_constituencies.copy()
all_constituencies['ADMK'] = admk_seats

# Color mapping
party_colors = {
    'ADMK': 'darkgreen',
    'BJP': 'orange',
    'PMK': 'yellow',       
    'AMMK': 'black',      
    'TMC': 'blue',
    'IJK': 'red',
    'TMMK': 'purple',
    'Puratchi Bharatham': 'darkred'
}

# --- Geocoding Function (Cached so it doesn't timeout on reload) ---
@st.cache_data(show_spinner=False)
def get_coordinates(seat_dict):
    geolocator = Nominatim(user_agent="tn_streamlit_mapper")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)
    
    locations = []
    
    # Progress bar for the first load
    progress_text = "Fetching GPS coordinates for the first time. Please wait..."
    my_bar = st.progress(0, text=progress_text)
    
    total_seats = sum(len(seats) for seats in seat_dict.values())
    current_seat = 0
    
    for party, places in seat_dict.items():
        color = party_colors.get(party, 'gray')
        for place in places:
            query = f"{place}, Tamil Nadu, India"
            try:
                loc = geocode(query)
                if loc:
                    locations.append({
                        "place": place,
                        "party": party,
                        "lat": loc.latitude,
                        "lon": loc.longitude,
                        "color": color
                    })
            except Exception as e:
                pass # Skip if API fails
            
            current_seat += 1
            my_bar.progress(current_seat / total_seats, text=f"Mapping {place}...")
            
    my_bar.empty()
    return locations

# --- Map Generation ---
with st.spinner('Building the map...'):
    mapped_data = get_coordinates(all_constituencies)
    
    # Initialize Folium Map
    tn_map = folium.Map(location=[10.8505, 78.4878], zoom_start=6)
    
    # Add markers
    for data in mapped_data:
        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=8,
            popup=f"<b>{data['place']}</b><br>Party: {data['party']}",
            tooltip=f"{data['place']} ({data['party']})",
            color=data["color"],
            fill=True,
            fill_color=data["color"],
            fill_opacity=0.9
        ).add_to(tn_map)

# --- Display in Streamlit ---
st_folium(tn_map, width=900, height=700)

# Sidebar stats
st.sidebar.header("Seat Breakdown")
for party, seats in all_constituencies.items():
    st.sidebar.markdown(f"**{party}:** {len(seats)} seats")
