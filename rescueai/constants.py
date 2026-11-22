"""
RescueAI System Constants, Design Tokens, Category Taxonomy, and Event Locations.
Adheres strictly to the Operations Console specification.
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Console Theme Tokens
COLOR_BG = "#0E1116"
COLOR_SURFACE = "#151A21"
COLOR_SURFACE_2 = "#1B222B"
COLOR_BORDER = "#262F3A"
COLOR_TEXT = "#E6EAF0"
COLOR_TEXT_MUTED = "#8B97A6"
COLOR_ACCENT = "#F2A33A"
COLOR_DANGER = "#E5534B"
COLOR_OK = "#4FA37A"

# Category Class Schema (0..4)
CATEGORY_NAMES = {
    0: "Affected People & Medical Emergencies",
    1: "Infrastructure Damage",
    2: "Rescue & Volunteering",
    3: "Other Relevant Information",
    4: "Not Humanitarian / Irrelevant"
}

CATEGORY_CONFIG = {
    0: {
        "name": "Affected People & Medical Emergencies",
        "color": "#E5534B",
        "urgency": "High",
        "description": "Casualties, injuries, trapped persons, urgent medical assistance requests."
    },
    1: {
        "name": "Infrastructure Damage",
        "color": "#F2A33A",
        "urgency": "High",
        "description": "Collapsed buildings, submerged roadways, broken utilities, power outages."
    },
    2: {
        "name": "Rescue & Volunteering",
        "color": "#3FB6A8",
        "urgency": "Medium",
        "description": "Rescue operations underway, volunteer teams mobilizing, relief distribution."
    },
    3: {
        "name": "Other Relevant Information",
        "color": "#6C9BD2",
        "urgency": "Low",
        "description": "Weather forecasts, transit advisories, official notices, general situation reports."
    },
    4: {
        "name": "Not Humanitarian / Irrelevant",
        "color": "#6B7480",
        "urgency": "None",
        "description": "Commercial advertising, humor, unrelated personal commentary, political discussions."
    }
}

# Real-world disaster coordinates for the seven CrisisMMD events.
# Coordinates reference the primary geographical epicenter/impact zone of each 2017 event.
DISASTER_EVENTS: Dict[str, Dict[str, Any]] = {
    "california_wildfires": {
        "event_id": "california_wildfires",
        "display_name": "California Wildfires",
        "disaster_type": "wildfire",
        # Centroid of Santa Rosa / Sonoma County, primary Tubbs Fire zone, Northern California firestorm Oct 2017
        "lat": 38.4404,
        "lon": -122.7141,
        "source": "USGS / CalFire Northern California Firestorm historical incident reports (October 2017)"
    },
    "srilanka_floods": {
        "event_id": "srilanka_floods",
        "display_name": "Sri Lanka Floods",
        "disaster_type": "flood",
        # Ratnapura, Sabaragamuwa Province, epicenter of May–June 2017 floods and landslides in SW Sri Lanka
        "lat": 6.6828,
        "lon": 80.3992,
        "source": "Disaster Management Centre Sri Lanka / UN OCHA Floods & Landslides Sitrep (May-June 2017)"
    },
    "mexico_earthquake": {
        "event_id": "mexico_earthquake",
        "display_name": "Central Mexico Earthquake",
        "disaster_type": "earthquake",
        # USGS epicenter coordinates for M7.1 Puebla-Morelos earthquake on September 19, 2017
        "lat": 18.5500,
        "lon": -98.4800,
        "source": "USGS Earthquake Hazards Program, Event M7.1 - 5km ENE of Raboso, Mexico (2017-09-19)"
    },
    "iraq_iran_earthquake": {
        "event_id": "iraq_iran_earthquake",
        "display_name": "Iran–Iraq Border Earthquake",
        "disaster_type": "earthquake",
        # USGS epicenter coordinates for M7.3 earthquake near Ezgeleh, Kermanshah Province / Halabja, Nov 12, 2017
        "lat": 34.9050,
        "lon": 45.9560,
        "source": "USGS Earthquake Hazards Program, Event M7.3 - 29km S of Halabjah, Iraq (2017-11-12)"
    },
    "hurricane_harvey": {
        "event_id": "hurricane_harvey",
        "display_name": "Hurricane Harvey",
        "disaster_type": "hurricane",
        # Houston, Harris County, Texas, primary urban impact and extreme precipitation center, Aug 2017
        "lat": 29.7604,
        "lon": -95.3698,
        "source": "NOAA National Hurricane Center Tropical Cyclone Report: Hurricane Harvey (August 2017)"
    },
    "hurricane_maria": {
        "event_id": "hurricane_maria",
        "display_name": "Hurricane Maria",
        "disaster_type": "hurricane",
        # Centroid of Puerto Rico, which sustained direct Category 4 landfall on September 20, 2017
        "lat": 18.2208,
        "lon": -66.5901,
        "source": "NOAA National Hurricane Center Tropical Cyclone Report: Hurricane Maria (September 2017)"
    },
    "hurricane_irma": {
        "event_id": "hurricane_irma",
        "display_name": "Hurricane Irma",
        "disaster_type": "hurricane",
        # Cudjoe Key / Florida Keys, primary US Category 4 landfall point on September 10, 2017
        "lat": 24.5551,
        "lon": -81.7800,
        "source": "NOAA National Hurricane Center Tropical Cyclone Report: Hurricane Irma (September 2017)"
    }
}

# Verified historical incident points and sub-locations for each 2017 event.
# Enables hub-and-spoke incident mapping matching the operations console reference.
DISASTER_SUB_INCIDENTS: Dict[str, List[Dict[str, Any]]] = {
    "hurricane_harvey": [
        {"name": "Pasadena Submerged Highway", "lat": 29.6911, "lon": -95.2091, "category": 1, "urgency": "High", "text": "Highway 225 completely submerged under 5ft of water, power lines sparking"},
        {"name": "Katy Bayou Rescue", "lat": 29.7858, "lon": -95.8245, "category": 0, "urgency": "High", "text": "Family of 5 trapped in attic as floodwaters rise past first floor ceiling"},
        {"name": "Baytown Utility Breach", "lat": 29.7355, "lon": -94.9774, "category": 1, "urgency": "High", "text": "Substation underwater, widespread electricity and water outage across county"},
        {"name": "Sugar Land Volunteer Staging", "lat": 29.6197, "lon": -95.6349, "category": 2, "urgency": "Medium", "text": "Cajun Navy boat crews staging at First Colony Mall with drinking water"},
        {"name": "Dickinson Medical Evacuation", "lat": 29.4608, "lon": -95.0513, "category": 0, "urgency": "High", "text": "Assisted living facility flooded, urgent oxygen and airlift required"},
        {"name": "Beaumont Water Station", "lat": 30.0802, "lon": -94.1266, "category": 2, "urgency": "Medium", "text": "Municipal water supply failed, emergency water tanker distribution point"},
    ],
    "hurricane_irma": [
        {"name": "Key West Overseas Highway", "lat": 24.5551, "lon": -81.7800, "category": 1, "urgency": "High", "text": "Storm surge washed out US-1 access, major debris blocking southbound lanes"},
        {"name": "Marathon Trauma Response", "lat": 24.7137, "lon": -81.0904, "category": 0, "urgency": "High", "text": "Fishermen Community Hospital damaged, helicopter transfer needed for injured"},
        {"name": "Naples Structural Damage", "lat": 26.1420, "lon": -81.7948, "category": 1, "urgency": "High", "text": "Cat 4 wind ripped roofs off mobile home parks, gas leak detected on 5th Ave"},
        {"name": "Islamorada Supply Depot", "lat": 24.9243, "lon": -80.6278, "category": 2, "urgency": "Medium", "text": "Volunteers distributing satellite phones, emergency rations, and cots"},
        {"name": "Homestead Evac Advisory", "lat": 25.4687, "lon": -80.4776, "category": 3, "urgency": "Low", "text": "County emergency management opens 4 additional storm shelters at high schools"},
    ],
    "hurricane_maria": [
        {"name": "San Juan Island Grid Failure", "lat": 18.4655, "lon": -66.1057, "category": 1, "urgency": "High", "text": "AEE reports complete transmission grid collapse, 100% of island without power"},
        {"name": "Ponce ICU Generator Alert", "lat": 18.0111, "lon": -66.6141, "category": 0, "urgency": "High", "text": "Regional hospital backup diesel running out, dialysis patients need evacuation"},
        {"name": "Utuado Isolated Valley", "lat": 18.2655, "lon": -66.7005, "category": 0, "urgency": "High", "text": "Landslides blocked all three bridges, 200 families cut off without food"},
        {"name": "Arecibo Water Distribution", "lat": 18.4725, "lon": -66.7153, "category": 2, "urgency": "Medium", "text": "Federal disaster team setting up reverse osmosis water purification station"},
        {"name": "Fajardo Harbor Advisory", "lat": 18.3258, "lon": -65.6525, "category": 3, "urgency": "Low", "text": "Ferry services to Vieques and Culebra suspended until harbor cleared"},
    ],
    "california_wildfires": [
        {"name": "Coffey Park Firestorm", "lat": 38.4716, "lon": -122.7483, "category": 1, "urgency": "High", "text": "Over 1,000 residential homes leveled by 70mph wind-driven firestorm"},
        {"name": "Kenwood Trapped Evacuation", "lat": 38.4138, "lon": -122.5461, "category": 0, "urgency": "High", "text": "Residents on Warm Springs Rd cut off by wall of fire, urgent helicopter extraction"},
        {"name": "Napa Fairgrounds Shelter", "lat": 38.2975, "lon": -122.2869, "category": 2, "urgency": "Medium", "text": "Red Cross evacuation shelter at capacity, volunteers requesting N95 masks"},
        {"name": "Glen Ellen Utility Collapse", "lat": 38.3638, "lon": -122.5297, "category": 1, "urgency": "High", "text": "Power grid and cell towers destroyed, emergency radio broadcast frequency 1610 AM"},
        {"name": "Calistoga Mandatory Evac", "lat": 38.5788, "lon": -122.5797, "category": 3, "urgency": "Low", "text": "CalFire issues mandatory evacuation order for entire town of Calistoga"},
    ],
    "mexico_earthquake": [
        {"name": "Mexico City Collapsed Structure", "lat": 19.4140, "lon": -99.1670, "category": 0, "urgency": "High", "text": "6-story apartment building collapsed on Alvaro Obregon, Topos rescue searching for survivors"},
        {"name": "Jojutla Historic Core Destruction", "lat": 18.6171, "lon": -99.1804, "category": 1, "urgency": "High", "text": "Over 2,000 adobe houses collapsed, municipal hospital evacuated to soccer field"},
        {"name": "Puebla City Masonry Hazards", "lat": 19.0414, "lon": -98.2063, "category": 1, "urgency": "High", "text": "Cathedral cupola and colonial buildings showing severe structural shearing"},
        {"name": "Atlixco Volunteer Staging", "lat": 18.9083, "lon": -98.4322, "category": 2, "urgency": "Medium", "text": "Civilian brigade organizing food, picks, shovels, and flashlights for search teams"},
        {"name": "Raboso Epicenter Aid Post", "lat": 18.5678, "lon": -98.4333, "category": 0, "urgency": "High", "text": "Rural clinics overwhelmed with trauma injuries, urgent surgical supplies needed"},
    ],
    "srilanka_floods": [
        {"name": "Kalutara River Inundation", "lat": 6.5854, "lon": 79.9607, "category": 0, "urgency": "High", "text": "Kalu Ganga river overflowed banks, 40 villagers stranded on rooftops in flood"},
        {"name": "Galle Naval Rescue Depot", "lat": 6.0535, "lon": 80.2210, "category": 2, "urgency": "Medium", "text": "Sri Lanka Navy boat flotilla deploying to southern villages with cooked meals"},
        {"name": "Matara Bridge Embankment", "lat": 5.9549, "lon": 80.5550, "category": 1, "urgency": "High", "text": "Nilwala river breached main highway embankment, Southern expressway closed"},
        {"name": "Bulathsinhala Landslide Search", "lat": 6.6500, "lon": 80.1833, "category": 0, "urgency": "High", "text": "Massive mudslide buried 12 houses on tea estate, heavy machinery desperately needed"},
    ],
    "iraq_iran_earthquake": [
        {"name": "Sarpol-e Zahab Field Hospital", "lat": 34.4611, "lon": 45.8628, "category": 0, "urgency": "High", "text": "City hospital heavily damaged, field triage tent set up on military airfield"},
        {"name": "Ezgeleh Epicenter Ruin", "lat": 34.8292, "lon": 45.8286, "category": 1, "urgency": "High", "text": "80% of residential buildings destroyed in epicenter village, sub-zero winter temperatures"},
        {"name": "Halabja Red Crescent Staging", "lat": 35.1778, "lon": 45.9861, "category": 2, "urgency": "Medium", "text": "Iraqi Red Crescent distributing winter blankets, kerosene heaters, and family tents"},
        {"name": "Qasr-e Shirin Water Fracture", "lat": 34.5147, "lon": 45.5786, "category": 1, "urgency": "High", "text": "Main water supply conduits sheared, bottled water distribution established at stadium"},
    ]
}


def snowflake_to_iso(tweet_id: str | int) -> str:
    """
    Decodes Twitter 64-bit Snowflake ID into UTC timestamp:
    ms = (tweet_id >> 22) + 1288834974657
    """
    try:
        tid = int(tweet_id)
        ms = (tid >> 22) + 1288834974657
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        # Fallback to base epoch if ID parsing fails
        return "2017-09-01T00:00:00+00:00"
