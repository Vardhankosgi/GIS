# ------------------- Import Libraries -------------------
import uuid
import re
import streamlit as st
import folium
import speech_recognition as sr
import osmnx as ox
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap

def show_disaster_map(disaster_type: str, region: str = "india"):
    import leafmap.foliumap as leafmap

    # Add more country-specific bounding boxes as needed
    bbox = {
        "india": [8.0, 68.0, 37.0, 97.0],
        "assam": [26.2, 89.7, 27.2, 93.6],
        "himachal": [31.0, 76.5, 32.7, 78.7],
        "nepal": [26.3, 80.0, 30.5, 88.2],
        "bangladesh": [20.5, 88.0, 26.5, 92.5],
        "pakistan": [23.6, 60.9, 36.8, 77.0],
        "sri lanka": [5.9, 79.3, 9.8, 82.0],
    }

    # Fallback region if unknown
    region_key = region.lower()
    if region_key not in bbox:
        region_key = "india"

    layer_defs = {
        "flood": {
            "url": "https://sedac.ciesin.columbia.edu/geoserver/wms",
            "layer": "ndh:ndh-flood-hazard-frequency-distribution",
            "name": "Flood Hazard"
        },
        "landslide": {
            "url": "https://sedac.ciesin.columbia.edu/geoserver/wms",
            "layer": "ndh:ndh-landslide-susceptibility-distribution",
            "name": "Landslide Hazard"
        },
        "fire": {
            "url": "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
            "layer": "MODIS_Terra_Thermal_Anomalies_Day",
            "name": "Active Fires (NASA)"
        }
    }

    hazard = layer_defs.get(disaster_type)
    if hazard is None:
        st.error("❌ Unknown disaster type.")
        return

    bounds = bbox[region_key]
    center_lat = (bounds[0] + bounds[2]) / 2
    center_lon = (bounds[1] + bounds[3]) / 2

    m = leafmap.Map(center=[center_lat, center_lon], zoom=6, basemap="CartoDB.Positron")


    m.add_wms_layer(
        url=hazard["url"],
        layers=hazard["layer"],
        name=hazard["name"],
        format="image/png",
        transparent=True
    )

    st.markdown(f"### 🗺️ {hazard['name']} Map ({region_key.capitalize()})")
    m.to_streamlit(height=600)


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


# ------------------- Global Hazard Map -------------------
def show_global_hazard_dashboard(focus="all"):
    st.markdown("## 🌐 Global Hazard Map (Color Highlighted)")

    m = leafmap.Map(center=[center_lat, center_lon], zoom=6, basemap="CartoDB.Positron")


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
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="ndh:ndh-landslide-susceptibility-distribution",
            name="⛰️ Landslide Susceptibility",
            format="image/png",
            transparent=True
        )

    # Optionally add population or elevation for context
    if focus == "all":
        m.add_wms_layer(
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="gpw-v4:gpw-v4-population-density_2020",
            name="👥 Population Density",
            format="image/png",
            transparent=True
        )

    m.to_streamlit(height=600)



# ------------------- Query Response -------------------
updated_keywords = {
    "hospital": {"amenity": "hospital"},
    "clinic": {"amenity": "clinic"},
    "atm": {"amenity": "atm"},
    "restaurant": {"amenity": "restaurant"},
    "bus stop": {"highway": "bus_stop"},
    "school": {"amenity": "school"}
}

def static_bot_response(message):
    msg = message.lower().strip()

    # Match exact friendly keywords
    for key in friendly_responses:
        if re.fullmatch(rf".*\b{re.escape(key)}\b.*", msg):
            return {"type": "text", "content": friendly_responses[key]}

    # POI map queries (school, hospital, etc.)
    for keyword, tags in updated_keywords.items():
        if keyword in msg and " in " in msg:
            return {
                "type": "dynamic_map",
                "query": msg,
                "tags": tags
            }

    # 🌐 Global Hazard Map Triggers
    if "global" in msg and ("hazard" in msg or "map" in msg):
        return {
            "type": "global_hazard_map",
            "content": "🌐 Global Hazard Overview"
        }
    elif "global" in msg and "fire" in msg:
        return {
            "type": "global_hazard_map",
            "content": "🔥 Global Fire Risk Map"
        }
    elif "global" in msg and "flood" in msg:
        return {
            "type": "global_hazard_map",
            "content": "🌊 Global Flood Hazard Map"
        }
    elif "global" in msg and "landslide" in msg:
        return {
            "type": "global_hazard_map",
            "content": "⛰️ Global Landslide Risk Map"
        }

    # 🗺️ Disaster maps by keyword
    if "flood" in msg:
        return {
            "type": "disaster_map",
            "disaster": "flood",
            "content": "🌊 Flood Hazard Zones in Assam"
        }
    elif "landslide" in msg:
        return {
            "type": "disaster_map",
            "disaster": "landslide",
            "content": "⛰️ Landslide Risk in Himachal Pradesh"
        }
    elif "fire" in msg:
        return {
            "type": "disaster_map",
            "disaster": "fire",
            "content": "🔥 Active Forest Fires across India"
        }

    # ❓ Help / Suggestions
    elif "help" in msg or "question" in msg:
        return {
            "type": "question",
            "questions": [
                "Where are the forest fire zones in India?",
                "Show me landslide risk areas in Himachal.",
                "Where are floods in Assam?",
                "Show rainfall intensity for July.",
                "Show traffic zones in India.",
                "Show hospitals in Kathmandu.",
                "Show schools in Itahari.",
                "Show global hazard map"
            ]
        }

    # Fallback generic text
    return {
        "type": "text",
        "content": "Hello! 👋 I'm your GIS assistant. Ask about floods, landslides, fires, rainfall, traffic, or POIs like clinics or schools."
    }


# ------------------- OSM Query -------------------
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

# ------------------- Sidebar -------------------
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

# ------------------- Handle Input -------------------
def handle_user_input(user_msg):
    chat_history.append({"role": "user", "type": "text", "content": user_msg})
    response = static_bot_response(user_msg)
    chat_history.append({"role": "bot", **response})

# ------------------- Display Chat -------------------
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
        
            # ✅ SAFELY initialize hazard_type
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
        
            # ✅ now safe to call
            show_global_hazard_dashboard(hazard_type)
        
            st.markdown(f"<span style='font-size:14px'>{msg.get('content','')}</span>", unsafe_allow_html=True)
            show_disaster_summary_table(hazard_type)

        
        elif msg["type"] == "disaster_map": 
            st.markdown(icon, unsafe_allow_html=True)
            st.markdown(f"**{msg['content']}**", unsafe_allow_html=True)
        
            # Show map and summary for disaster type (e.g. flood, landslide, fire)
            show_disaster_map(msg["disaster"], msg.get("region", "india"))
            show_disaster_summary_table(msg["disaster"])


# ------------------- Input Field -------------------
user_input = st.chat_input("Type your question here...")
if user_input:
    handle_user_input(user_input)
    st.rerun()

# ------------------- Voice Input -------------------
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
