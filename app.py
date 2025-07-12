# ------------------- Import Libraries -------------------
import uuid
import re
import streamlit as st
import folium
import speech_recognition as sr
import osmnx as ox
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap

# --- Local GeoJSON data for demonstration ---
FLOOD_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.25, 9.95], [76.30, 9.95], [76.30, 10.05], [76.25, 10.05], [76.25, 9.95]]]
            },
            "properties": {"risk_level": "High"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.35, 9.85], [76.40, 9.85], [76.40, 9.95], [76.35, 9.95], [76.35, 9.85]]]
            },
            "properties": {"risk_level": "Medium"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.45, 9.75], [76.50, 9.75], [76.50, 9.85], [76.45, 9.85], [76.45, 9.75]]]
            },
            "properties": {"risk_level": "Low"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.22, 10.02], [76.28, 10.02], [76.28, 10.08], [76.22, 10.08], [76.22, 10.02]]]
            },
            "properties": {"risk_level": "High"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.42, 9.78], [76.48, 9.78], [76.48, 9.88], [76.42, 9.88], [76.42, 9.78]]]
            },
            "properties": {"risk_level": "Low"}
        }
    ]
}

LANDSLIDE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[93.7, 25.8], [93.8, 25.8], [93.8, 25.9], [93.7, 25.9], [93.7, 25.8]]]
            },
            "properties": {"risk_level": "High"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[93.6, 25.7], [93.7, 25.7], [93.7, 25.8], [93.6, 25.8], [93.6, 25.7]]]
            },
            "properties": {"risk_level": "Medium"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[93.72, 25.85], [93.78, 25.85], [93.78, 25.95], [93.72, 25.95], [93.72, 25.85]]]
            },
            "properties": {"risk_level": "High"}
        }
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
    "hello": "Hi there! 😊 I'm here to help with hazard zones and local planning maps.",
    "how are you": "I'm running smoothly! Ask about geographic risks or features.",
    "how can you help": "You can ask things like 'Where are floods in Assam?' or 'Landslide risk in Himachal?'.",
    "what can you do": "I show hazard maps, rainfall patterns, school & clinic locations, and more!",
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
def create_disaster_map(disaster_type: str, region: str = "india"):
    bbox = {
        "india": [8.0, 68.0, 37.0, 97.0],
        "assam": [26.2, 89.7, 27.2, 93.6],
        "himachal": [31.0, 76.5, 32.7, 78.7],
        "nepal": [26.3, 80.0, 30.5, 88.2],
        "bangladesh": [20.5, 88.0, 26.5, 92.5],
        "pakistan": [23.6, 60.9, 36.8, 77.0],
        "sri lanka": [5.9, 79.3, 9.8, 82.0],
    }
    
    region_key = region.lower()
    bounds = bbox.get(region_key, bbox["india"])
    center_lat = (bounds[0] + bounds[2]) / 2
    center_lon = (bounds[1] + bounds[3]) / 2
    zoom_level = 6
    if region_key == "india":
        zoom_level = 4
    
    m = leafmap.Map(center=[center_lat, center_lon], zoom=zoom_level, basemap="CartoDB.Positron")
    
    if disaster_type == "flood":
        st.markdown("🚨 **Note:** This map uses local data for demonstration to ensure the colors appear.")
        style_function = lambda x: {
            "fillColor": "red" if x["properties"]["risk_level"] == "High" else 
                         "orange" if x["properties"]["risk_level"] == "Medium" else 
                         "lightblue",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6
        }
        geojson_layer = folium.GeoJson(FLOOD_GEOJSON, name="Flood Risk", style_function=style_function).add_to(m)
        m.fit_bounds(geojson_layer.get_bounds())
        
    elif disaster_type == "landslide":
        st.markdown("🚨 **Note:** This map uses local data for demonstration to ensure the colors appear.")
        style_function = lambda x: {
            "fillColor": "darkred" if x["properties"]["risk_level"] == "High" else 
                         "darkorange" if x["properties"]["risk_level"] == "Medium" else 
                         "yellow",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6
        }
        geojson_layer = folium.GeoJson(LANDSLIDE_GEOJSON, name="Landslide Risk", style_function=style_function).add_to(m)
        m.fit_bounds(geojson_layer.get_bounds())
        
    elif disaster_type == "fire":
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            layers="MODIS_Terra_Thermal_Anomalies_Day",
            name="🔥 Forest Fires (NASA MODIS)",
            format="image/png",
            transparent=True
        )
    else:
        st.error("❌ Unknown disaster type.")
        return None
        
    return m

def show_disaster_summary_table(hazard_type: str):
    st.markdown("### 📊 Disaster Summary Table")
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
    center_lon = 80.0
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

def static_bot_response(message):
    msg = message.lower().strip()
    for key in friendly_responses:
        if re.fullmatch(rf".*\b{re.escape(key)}\b.*", msg):
            return {"type": "text", "content": friendly_responses[key]}
    for keyword, tags in updated_keywords.items():
        if keyword in msg and " in " in msg:
            return {
                "type": "dynamic_map",
                "query": msg,
                "tags": tags
            }
    if "global hazard" in msg or "all hazards" in msg or "overall risk" in msg:
        return {
            "type": "global_hazard_map",
            "content": "🌐 Global Hazard Map"
        }
    if "flood" in msg:
        return {
            "type": "disaster_map",
            "disaster": "flood",
            "content": "🌊 Flood Hazard Zones in India"
        }
    elif "landslide" in msg:
        return {
            "type": "disaster_map",
            "disaster": "landslide",
            "content": "⛰️ Landslide Hazard Zones in India"
        }
    elif "fire" in msg or "forest fire" in msg:
        return {
            "type": "disaster_map",
            "disaster": "fire",
            "content": "🔥 Forest Fire Risk Zones in India"
        }
    if "help" in msg or "question" in msg:
        return {
            "type": "question",
            "questions": [
                "Show global hazard map",
                "Show flood risk areas",
                "Where are forest fires?",
                "Landslide-prone regions in Himachal?",
                "Show schools in Kathmandu"
            ]
        }
    return {
        "type": "text",
        "content": "Hello! 👋 I'm your GIS assistant. Ask about floods, landslides, fires, rainfall, or POIs like schools or hospitals."
    }

def get_osm_map_from_query(query, tags):
    try:
        place = query.split(" in ")[-1].strip().capitalize()
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
        return None, f"❌ Error retrieving map: {str(e)}"

# ------------------- Streamlit UI -------------------
st.set_page_config("GIS Assistant", layout="wide")
st.markdown("<h2 style='text-align: center;'>🚁 GIS Map Assistant</h2>", unsafe_allow_html=True)
st.caption("Ask questions like 'Show rainfall in Kochi', 'Landslide in Dima Hasao', or 'Global hazard map'")

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.conversations[new_id] = []
    st.session_state.current_chat_id = new_id

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

st.markdown("---")
for msg in chat_history:
    is_bot = msg["role"] == "bot"
    col1, col2 = st.columns([6, 6])
    with (col1 if is_bot else col2):
        icon = "<span style='font-size:30px;'>🤖</span>" if is_bot else "<span style='font-size:30px;'>🙋</span>"
        if msg["type"] == "text":
            st.markdown(f"{icon} <span style='font-size:14px'>{msg['content']}</span>", unsafe_allow_html=True)
        elif msg["type"] == "dynamic_map":
            map_obj, summary = get_osm_map_from_query(msg["query"], msg["tags"])
            if map_obj:
                st.markdown(icon, unsafe_allow_html=True)
                st_data = st_folium(map_obj, width=700, height=500)
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
            show_global_hazard_dashboard(hazard_type)
            st.markdown(f"<span style='font-size:14px'>{msg.get('content','')}</span>", unsafe_allow_html=True)
            show_disaster_summary_table(hazard_type)
    
        elif msg["type"] == "disaster_map":
            st.markdown(icon, unsafe_allow_html=True)
            map_col, table_col = st.columns(2)
            with map_col:
                st.markdown(f"### 🗺️ {msg['disaster'].capitalize()} Risk Map")
                map_obj = create_disaster_map(msg["disaster"], msg.get("region", "india"))
                if map_obj:
                    st_folium(map_obj, width=700, height=500)
            with table_col:
                st.markdown("### 📊 Disaster Summary Table")
                show_disaster_summary_table(msg["disaster"])

user_input = st.chat_input("Type your question here...")
if user_input:
    handle_user_input(user_input)
    st.rerun()

st.markdown("🎤 Or use your voice:")
if st.button("🎤 Start Voice Input"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak now.")
        try:
            audio = recognizer.listen(source, timeout=5)
            voice_text = recognizer.recognize_google(audio)
            st.success(f"🗣️ You said: `{voice_text}`")
            handle_user_input(voice_text)
            st.rerun()
        except sr.WaitTimeoutError:
            st.warning("⏱️ No speech detected. Try again.")
        except sr.UnknownValueError:
            st.error("🤷 Could not understand audio.")
        except sr.RequestError as e:
            st.error(f"⚠️ Error with speech recognition: {e}")
