# ------------------- Import Libraries -------------------
import uuid
import re
import streamlit as st
import folium
import speech_recognition as sr
import osmnx as ox
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap
import platform
import av
import io
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import tempfile
import random

# --- Local GeoJSON data for demonstration (now with Points) ---
FLOOD_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.28, 9.98]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.32, 10.03]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.38, 9.89]}, "properties": {"risk_level": "Medium"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.45, 9.81]}, "properties": {"risk_level": "Low"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.24, 10.05]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.40, 9.77]}, "properties": {"risk_level": "Low"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [76.31, 9.91]}, "properties": {"risk_level": "Medium"}}
    ]
}

LANDSLIDE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.75, 25.85]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.79, 25.89]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.65, 25.75]}, "properties": {"risk_level": "Medium"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.78, 25.92]}, "properties": {"risk_level": "High"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [93.68, 25.82]}, "properties": {"risk_level": "Medium"}}
    ]
}

# ------------------- Static Response Data -------------------
info_map = {
    "forest_fire": "🔥 **Forest Fire Risk Zones:** Areas in red are highly susceptible due to vegetation and dry climate.",
    "landslide": "⛰️ **Landslide Hazard Map:** Sloped regions vulnerable during monsoon are marked.",
    "flood": "🌊 **Flood Hazard Zones:** Frequently affected low-lying areas.",
    "global_hazard": "🌐 **Live Hazard Intelligence:** Real-time global view of wildfire, flood, landslide, and population data."
}

friendly_responses = {
    "hi": "Hello! 👋 I'm your GIS assistant. Ask me about rainfall, landslides, floods, clinics, or schools.",
    "how are you": "I'm running smoothly! Ask about geographic risks or features.",
    "how can you help": "You can ask things like 'Where are floods in Assam?' or 'Landslide risk in Himachal?'.",
    "thanks": "You're welcome! Let me know if you need anything else."
}


updated_keywords = {
    "hospital": {"amenity": "hospital"},
    "clinic": {"amenity": "clinic"},
    "atm": {"amenity": "atm"},
    "restaurant": {"amenity": "restaurant"},
    "bus stop": {"highway": "bus_stop"},
    "school": {"amenity": "school"}
}

# ------------------- Functions -------------------
def create_disaster_map(disaster_type: str, region: str = "world"):
    try:
        # Attempt to geocode the specified region
        gdf = ox.geocode_to_gdf(region)
        center_lat = gdf.geometry.centroid.y.values[0]
        center_lon = gdf.geometry.centroid.x.values[0]
        if region.lower() in ["india", "himachal pradesh", "kerala", "nepal", "itahari","kochi"]:
            zoom_level = 6
        elif region.lower() in ["world", "global"]:
            zoom_level = 8
        else:
            zoom_level = 10  # Closer zoom for country-specific views

        st.info(f"📍 Displaying map centered on {region.title()}.")
    except Exception:
        # Fallback to a global view if geocoding fails.
        center_lat = 20.0
        center_lon = 0.0
        zoom_level = 2
        st.warning(f"⚠️ Could not geocode location '{region}'. Showing a global map instead.")

    m = leafmap.Map(center=[center_lat, center_lon], zoom=zoom_level, basemap="CartoDB.Positron")

    color_map = {"High": "red", "Medium": "orange", "Low": "lightblue"}

    if disaster_type == "flood":
        st.markdown("🌊 **Flood Hazard Map**")
        m.add_wms_layer(
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="ndh:ndh-flood-hazard-frequency-distribution",
            name="Flood Risk (Live)",
            format="image/png",
            transparent=True
        )
    
        if region.lower() in ["india", "himachal pradesh", "kerala", "nepal", "itahari","kochi"]:

            legend_html = """
            <div style='position: fixed; bottom: 30px; left: 30px; width: 200px; height: 100px;
                 background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                 padding: 10px;'>
            <b>Flood Risk Legend</b><br>
            🟥 High Risk<br>
            🟧 Medium Risk<br>
            🟦 Low Risk
            </div>
            """
            m.add_child(folium.map.LayerControl())
            
            for feature in FLOOD_GEOJSON["features"]:
                lon, lat = feature["geometry"]["coordinates"]
                risk_level = feature["properties"]["risk_level"]
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=12,
                    color="black",
                    weight=1,
                    fill_color=color_map[risk_level],
                    fill_opacity=0.7,
                    tooltip=f"{risk_level} Flood Risk"
                ).add_to(m)
            
            m.get_root().html.add_child(folium.Element(legend_html))


    elif disaster_type == "landslide":
        st.markdown("⛰️ **Landslide Hazard Map**")
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            layers="Global_Landslide_Hazard_Map",
            name="Landslide Susceptibility (Live)",
            format="image/png",
            transparent=True
        )
        if region.lower() in ["india", "himachal pradesh", "kerala", "nepal", "itahari","kochi"]:    

            legend_html = """
            <div style='position: fixed; bottom: 30px; left: 30px; width: 200px; height: 100px;
                 background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                 padding: 10px;'>
            <b>Flood Risk Legend</b><br>
            🟥 High Risk<br>
            🟧 Medium Risk<br>
            🟦 Low Risk
            </div>
            """
            m.add_child(folium.map.LayerControl())
            
            for feature in LANDSLIDE_GEOJSON["features"]:

                lon, lat = feature["geometry"]["coordinates"]
                risk_level = feature["properties"]["risk_level"]
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=12,
                    color="black",
                    weight=1,
                    fill_color=color_map[risk_level],
                    fill_opacity=0.7,
                    tooltip=f"{risk_level} Landslide Risk"

                ).add_to(m)
            
            m.get_root().html.add_child(folium.Element(legend_html))
            

    elif disaster_type == "fire":
        st.markdown("🔥 **Forest Fire Risk Map**")
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            layers="MODIS_Terra_Thermal_Anomalies_Day",
            name="Forest Fires (Live)",
            format="image/png",
            transparent=True
        )

    else:
        st.error("❌ Unknown disaster type.")
        return None

    return m


def show_disaster_summary_table(hazard_type: str):
    if hazard_type == "landslide":
        st.dataframe({
            "Location": ["Bharmour", "Manikaran", "Kufri", "Rajgarh", "Jogindernagar"],
            "Slope (°)": [35, 42, 28, 39, 25],
            "Soil Type": ["Sandy Loam", "Silty Clay", "Loam", "Gravel", "Sandy Clay"],
            "Rainfall (mm)": [1950, 2300, 1650, 2100, 1750],
            "Frequency/Year": [4, 6, 2, 5, 1],
            "Risk Level": ["High", "Very High", "Medium", "High", "Low"]
        }, use_container_width=True)
    elif hazard_type == "flood":
        st.dataframe({
            "District": ["Barpeta", "Dhemaji", "Kochi", "Patna", "Guwahati"],
            "Flood Level": ["Severe", "High", "Moderate", "Severe", "Moderate"],
            "Displaced": [23000, 15000, 8000, 12000, 9000],
            "Rainfall (mm)": [2200, 2100, 1800, 2400, 1900],
            "Relief Camps": [25, 18, 12, 22, 15]
        }, use_container_width=True)
    elif hazard_type == "fire":
        st.dataframe({
            "Region": ["Shimla", "Chamba", "Sirmaur", "Kullu", "Mandi"],
            "Avg Temp (°C)": [35, 34, 36, 33, 32],
            "Incidents": [45, 30, 25, 40, 38],
            "High Risk Zones": ["Yes", "Yes", "No", "Yes", "Yes"]
        }, use_container_width=True)
    elif hazard_type == "traffic":
        st.dataframe({
            "City": ["Delhi", "Mumbai", "Chennai", "Bengaluru", "Hyderabad"],
            "Peak Congestion (%)": [78, 72, 65, 80, 69],
            "Delay (min/km)": [6.5, 5.8, 5.2, 7.0, 6.0],
            "Traffic Zones": ["Ring Rd", "Western Exp", "Anna Salai", "Outer Ring Rd", "Hitec City"]
        }, use_container_width=True)

def show_global_hazard_dashboard(focus="all"):
    st.markdown("## 🌐 Global Hazard Map (Color Highlighted)")
    center_lat = 20.0
    center_lon = 0.0
    m = leafmap.Map(center=[center_lat, center_lon], zoom=2, basemap="CartoDB.Positron")
    if focus in ["all", "fire"]:
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi",
            layers="MODIS_Terra_Thermal_Anomalies_Day",
            name="🔥 Fire Risk (MODIS)",
            format="image/png",
            transparent=True
        )
    if focus in ["all", "flood"]:
        m.add_wms_layer(
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="ndh:ndh-flood-hazard-frequency-distribution",
            name="🌊 Flood Risk (Color)",
            format="image/png",
            transparent=True
        )
    if focus in ["all", "landslide"]:
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            layers="Global_Landslide_Hazard_Map",
            name="⛰️ Landslide Susceptibility",
            format="image/png",
            transparent=True
        )
    if focus == "all":
        m.add_wms_layer(
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="gpw-v4:gpw-v4-population-density_2020",
            name="👥 Population Density",
            format="image/png",
            transparent=True
        )
    m.to_streamlit(height=600)


# ------------------- Corrected Functions -------------------
def static_bot_response(message):

    msg = message.lower().strip()
    normalized_msg = re.sub(r'[^\w\s]', '', msg)

    # 1. Define known and fallback regions early
    known_regions = [
        "india", "china", "russia", "brazil", "usa", "indonesia",
        "nepal", "bangladesh", "pakistan", "himachal pradesh",
        "kerala", "kochi", "itahari"
    ]
    default_regions = ["world", "global"]
    
    # 2. Check for Specific Disaster intents first (HIGH PRIORITY)
    # This prevents generic greetings from overriding a specific request.
    disaster_aliases = {
        "flood": [r"\bflood(?:s|ing)?\b"],
        "landslide": [
            r"\blandslides?\b",
            r"\bland[\s\-]?slides?\b",
            r"\bland\s+slide(?:s)?\b",
            r"\bmudslides?\b"
        ],
        "fire": [
            r"\bforest\s*fires?\b",
            r"\bwild[\s\-]?fires?\b"
        ]
    }

    for disaster, patterns in disaster_aliases.items():
        for pattern in patterns:
            match = re.search(rf"{pattern}(?:.*?\s+in\s+([a-zA-Z\s]+))?", msg)
            if match:
                region = match.group(1).strip().lower() if match.lastindex and match.group(1) else random.choice(known_regions)
                return {
                    "type": "disaster_map",
                    "disaster": disaster,
                    "region": region,
                    "content": f"🗺️ {disaster.capitalize()} Hazard Zones in {region.title()}"
                }

    # 3. Check for POIs (schools, hospitals, etc.) (MEDIUM PRIORITY)
    for keyword, tags in updated_keywords.items():
        if re.search(rf"\b{keyword}s?\b", msg):
            match = re.search(rf"\b{keyword}s?\b\s*(in\s+([a-z\s]+))?", msg)
            region = match.group(2).strip().lower() if match and match.group(2) else "world"

            return {
                "type": "dynamic_map",
                "query": f"{keyword} in {region}",
                "tags": tags
            }

    # 4. Check for Global dashboard (MEDIUM PRIORITY)
    if "global hazard" in msg or "all hazards" in msg or "overall risk" in msg:
        return {
            "type": "global_hazard_map",
            "content": "🌐 Global Hazard Map"
        }

    # 5. Check for Help intent (LOW PRIORITY)
    if "help" in msg or "question" in msg:
        help_text = """
        **Here's what I am capable of answering:**
        
        --1. For Finding Local Places--
        * What it does: Helps you find nearby places like hospitals, schools, and restaurants on a map.
        * Keywords: hospital, school, clinic, atm, restaurant
        
        --2. For Hazard & Disaster Information--
        * What it does: Displays maps and data tables for specific hazards.
        * Keywords: flood, landslide, fire, global hazard
        
        --3. For General Interaction--
        * What it does: Provides friendly responses and general information about the bot.
        * Keywords: hi, hello, how can you help, what can you do
        """
        return {"type": "text", "content": help_text}

    # 6. Check for Friendly greetings (LOWEST PRIORITY)
    # Using re.fullmatch ensures the user's message is *only* a greeting.
    friendly_variants = {
        "hi": ["hi", "hii", "hey", "hello", "heyy"],
        "how are you": ["how are you", "how r u", "how are u"],
        "how can you help": ["how can you help", "what can you do"],
        "thanks": ["thanks", "thank you", "thx"]
    }
    for key, variants in friendly_variants.items():
        for phrase in variants:
            if re.fullmatch(phrase, normalized_msg):
                return {"type": "text", "content": friendly_responses.get(key)}


    # 7. Fallback if no intent is matched
    fallback_disaster = random.choice(list(disaster_aliases.keys()))
    fallback_region = random.choice(known_regions + default_regions)
    return {
        "type": "disaster_map",
        "disaster": fallback_disaster,
        "region": fallback_region,
        "content": f"🗺️ {fallback_disaster.capitalize()} Hazard Zones in {fallback_region.title()}"
    }

def get_osm_map_from_query(query, tags):
    try:
        place = query.split(" in ")[-1].strip()
        gdf = ox.features_from_place(place, tags)
        
        if gdf.empty:
            return None, f"⚠️ No data found for {list(tags.values())[0]} in {place}."
        
        gdf = gdf[gdf.geometry.type.isin(['Point', 'Polygon'])]
        gdf['lon'] = gdf.geometry.centroid.x
        gdf['lat'] = gdf.geometry.centroid.y
        m = folium.Map(location=[gdf['lat'].mean(), gdf['lon'].mean()], zoom_start=13)
        
        for _, row in gdf.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=row.get('name', 'Unnamed'),
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)
        label = list(tags.values())[0].capitalize()
        return m, f"📍 **{label}s in {place}:** Retrieved live from OpenStreetMap."
    except Exception as e:
        return None, f"❌ Error retrieving map for '{place}'. Please try a more specific location. Error: {str(e)}"

# ------------------- Streamlit UI -------------------
st.set_page_config("GIS Assistant", layout="wide")
st.markdown("<h2 style='text-align: center;'>🌐 GIS Bot Assistant</h2>", unsafe_allow_html=True)
st.caption("Ask me anything related to disaster risks, emergency zones, or map-based hazard insights—I'm here to assist with all your geospatial questions")

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.conversations[new_id] = []
    st.session_state.current_chat_id = new_id
if 'last_transcription' not in st.session_state:
    st.session_state.last_transcription = None

chat_id = st.session_state.current_chat_id
chat_history = st.session_state.conversations[chat_id]

st.sidebar.header("💬 Chat Sessions")
for cid in st.session_state.conversations:
    if st.sidebar.button(f"Chat {cid[:6]}", key=cid):
        st.session_state.current_chat_id = cid
        st.rerun()
if st.sidebar.button("➕ New Chat"):
    new_id = str(uuid.uuid4())
    st.session_state.conversations[new_id] = []
    st.session_state.current_chat_id = new_id
    st.rerun()

def handle_user_input(user_msg):
    chat_history.append({"role": "user", "type": "text", "content": user_msg})
    response = static_bot_response(user_msg)
    chat_history.append({"role": "bot", **response})

for msg in chat_history:
    is_bot = msg["role"] == "bot"
    col1, col2 = st.columns([6, 6])
    with (col1 if is_bot else col2):
        icon = "<span style='font-size:30px;'>🤖</span>" if is_bot else "<span style='font-size:30px;'>🙋</span>"
        if msg["type"] == "text":
            st.markdown(f"{icon} <span style='font-size:14px'>{msg['content']}</span>", unsafe_allow_html=True)
        
        elif msg["type"] == "dynamic_map":
            st.markdown(icon, unsafe_allow_html=True)
            map_obj, summary = get_osm_map_from_query(msg["query"], msg["tags"])
            if map_obj:
                st_data = st_folium(map_obj, key=f"map_{chat_id}_osm_{chat_history.index(msg)}", width=700, height=500)
                st.markdown(f"<span style='font-size:14px'>{summary}</span>", unsafe_allow_html=True)
            else:
                st.error(summary)
        
        elif msg["type"] == "global_hazard_map":
            st.markdown(icon, unsafe_allow_html=True)
            hazard_type = "all"
            content = msg.get("content", "").lower() if "content" in msg else ""
            if "flood" in content:
                hazard_type = "flood"
            elif "landslide" in content:
                hazard_type = "landslide"
            elif "fire" in content or "forest" in content:
                hazard_type = "fire"
            elif "traffic" in content:
                hazard_type = "traffic"
            
            with st.container():
                show_global_hazard_dashboard(hazard_type)
            
            st.markdown(f"<span style='font-size:14px'>{msg.get('content','')}</span>", unsafe_allow_html=True)
            show_disaster_summary_table(hazard_type)
        
        elif msg["type"] == "disaster_map":
            st.markdown(icon, unsafe_allow_html=True)
            
            map_obj = create_disaster_map(msg["disaster"], msg.get("region", "world"))
            if map_obj:
                map_col, table_col = st.columns([1, 1])  
                with map_col:
                    st.markdown(f"### 🗺️ {msg['disaster'].capitalize()} Risk Map")
                    st_folium(map_obj, key=f"folium_{chat_id}_{chat_history.index(msg)}", height=500, use_container_width=True)

                
                with table_col:
                    st.markdown(f"### 📊 {msg['disaster'].capitalize()} Summary Table")
                    show_disaster_summary_table(msg["disaster"])

# ------------------- Input Field -------------------
user_input = st.chat_input("Type your question here...")
if user_input:
    handle_user_input(user_input)
    st.rerun()

