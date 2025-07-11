import streamlit as st
import uuid
from PIL import Image
import speech_recognition as sr
import osmnx as ox
import folium
import geopandas as gpd
from shapely.geometry import Point
from streamlit_folium import st_folium
import re

# ---------------- Image & Summary ------------------
image_map = {
    "forest_fire": "assets/forest_fire.jpg",
    "landslide": "assets/landslide_hazard.jpg",
    "rainfall_kochi": "assets/rainfall_kochi.jpg",
    "flood_kochi": "assets/flood_map_kochi.png",
    "clinic_locations": "assets/clinic_locations.jpg",
    "assam_flood_map": "assets/assam_flood_map.png",
    "barpeta_flood": "assets/flood_map_kochi.png",
    "dimapur_landslide": "assets/dimapur_landslide_map.png",
    "rainfall_july": "assets/southplains_loop_20190707_2328Z.gif",
    "traffic": "assets/image.png",
}

info_map = {
    "forest_fire": "🔥 **Forest Fire Risk Zones:** Areas in red are highly susceptible due to vegetation and dry climate.",
    "landslide": "⛰️ **Landslide Hazard Map:** Sloped regions vulnerable during monsoon are marked.",
    "rainfall_kochi": "🌧️ **Rainfall Pattern:** Shows rainfall intensity; peak in June–August.",
    "flood_kochi": "🌊 **Flood Risk:** Low-lying, poor drainage areas are flood-prone.",
    "clinic_locations": "🏥 **Clinics:** Plots hospitals and clinics for public access.",
    "assam_flood_map": "🌊 **Flood & Landslide:** Aggregated flood-prone zones and high-risk landslide districts (2021–23).",
    "barpeta_flood": "🚨 **Severe Floods:** Areas in red faced major waterlogging and displacement.",
    "dimapur_landslide": "🪨 **Landslide Risk:** Steep terrain and rainfall contribute to hazard levels.",
    "rainfall_july": "🌦️ **Rainfall:** Shows districts with exceptionally high rainfall events.",
    "traffic": "🚦 **High Traffic Areas:** Shows districts with exceptionally high traffic.",
}

friendly_responses = {
    "hi": "Hello! 👋 I'm your GIS assistant. Ask me about rainfall, landslides, floods, clinics, or schools.",
    "hello": "Hi there! 😊 I'm here to help with hazard zones and local planning maps.",
    "how are you": "I'm running smoothly! Ask about geographic risks or features.",
    "how can you help": "You can ask things like 'Where are floods in Assam?' or 'Landslide risk in Himachal?'.",
    "what can you do": "I show hazard maps, rainfall patterns, school & clinic locations, and more!",
    "thanks": "You're welcome! Let me know if you need anything else.",
}

# ---------------- Dynamic OSM Map ------------------
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

# ---------------- Static Response Logic ------------------

# Add this at top level (global)
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

    # Check if the message matches known POI types and includes a location
    for keyword, tags in updated_keywords.items():
        if keyword in msg and " in " in msg:
            return {
                "type": "dynamic_map",
                "query": msg,
                "tags": tags
            }

    # Image map matches
    if "forest fire" in msg:
        return respond_with("forest_fire")
    elif "landslide" in msg:
        if "dima" in msg:
            return respond_with("dimapur_landslide")
        return respond_with("landslide")
    elif "rainfall" in msg and "kochi" in msg:
        return respond_with("rainfall_kochi")
    elif "rainfall" in msg and "july" in msg:
        return respond_with("rainfall_july")
    elif "traffic" in msg:
        return respond_with("traffic")
    elif "flood" in msg and "kochi" in msg:
        return respond_with("flood_kochi")
    elif "flood" in msg and "barpeta" in msg:
        return respond_with("barpeta_flood")
    elif "assam" in msg and "flood" in msg:
        return respond_with("assam_flood_map")

    # Help or questions
    elif "help" in msg or "question" in msg:
        return {
            "type": "question",
            "questions": [
                "Where are the forest fire zones in Himachal?",
                "Show me landslide risk areas in Assam.",
                "How is rainfall distributed in Kochi?",
                "Which parts of Kochi are flood-prone?",
                "Where are the schools located in Itahari?",
                "Show hospitals and clinics in Itahari.",
                "Display severe floods in Barpeta during 2023.",
                "Is Dima Hasao at landslide risk?",
                "Show districts with rainfall above 500mm in July.",
                "Show overall flood-prone regions in Assam.",
                "Show hospitals in Kathmandu",
                "Show ATMs in Delhi",
                "Show restaurants in Mumbai",
                "Show bus stops in Chennai"
            ]
        }

    return {
        "type": "text",
        "content": "Hello! 👋 I'm your GIS assistant. Ask me about rainfall, landslides, floods, clinics, schools, fire zones, rainfall, floods, POIs like hospitals or ATMs."
    }

def respond_with(key):
    return {"type": "image_summary", "image": image_map[key], "summary": info_map[key]}

# ---------------- Streamlit UI Setup ------------------
st.set_page_config("GIS Assistant", layout="wide")
st.markdown("<h2 style='text-align: center;'>🚁 GIS Map Assistant</h2>", unsafe_allow_html=True)
st.caption("Ask questions like 'Show rainfall in Kochi', 'Landslide in Dima Hasao', or 'Hospitals in Itahari'")

# ---------------- Chat Session Setup ------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.conversations[new_id] = []
    st.session_state.current_chat_id = new_id

chat_id = st.session_state.current_chat_id
chat_history = st.session_state.conversations[chat_id]

# ---------------- Sidebar ------------------
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

# ---------------- Handle Input ------------------
def handle_user_input(user_msg):
    chat_history.append({"role": "user", "type": "text", "content": user_msg})
    response = static_bot_response(user_msg)
    chat_history.append({"role": "bot", **response})

# ---------------- Display Chat ------------------
# ---------------- Display Chat ------------------
st.markdown("---")
for msg in chat_history:
    is_bot = msg["role"] == "bot"
    col1, col2 = st.columns([6, 6])
    with (col1 if is_bot else col2):
        icon = "<span style='font-size:30px;'>🤖</span>" if is_bot else "<span style='font-size:30px;'>🙋</span>"

        if msg["type"] == "text":
            st.markdown(f"{icon} <span style='font-size:14px'>{msg['content']}</span>", unsafe_allow_html=True)

        elif msg["type"] == "image_summary":
            st.markdown(icon, unsafe_allow_html=True)
            with st.container():
                col_img, col_summary = st.columns([1, 1])
                with col_img:
                    image_path = msg.get("image")
                    if image_path and os.path.exists(image_path):
                        st.image(Image.open(image_path), use_container_width=True)
                    else:
                        st.error("❌ Image not found or invalid path.")

                with col_summary:
                    st.markdown(f"<span style='font-size:14px'>{msg['summary']}</span>", unsafe_allow_html=True)

                    # Extra data summaries by keyword
                    if "landslide" in msg["image"]:
                        st.markdown("#### 📊 Landslide Risk Table (Sample)")
                        st.dataframe({
                            "Location": ["Bharmour", "Manikaran", "Kufri", "Rajgarh", "Jogindernagar"],
                            "Slope (°)": [35, 42, 28, 39, 25],
                            "Soil Type": ["Sandy Loam", "Silty Clay", "Loam", "Gravel", "Sandy Clay"],
                            "Rainfall (mm)": [1950, 2300, 1650, 2100, 1750],
                            "Frequency/Year": [4, 6, 2, 5, 1],
                            "Risk Level": ["High", "Very High", "Medium", "High", "Low"]
                        }, use_container_width=True)

                    elif "flood" in msg["image"]:
                        st.markdown("#### 📊 Flood Summary Table (Sample)")
                        st.dataframe({
                            "District": ["Barpeta", "Dhemaji", "Kochi", "Patna", "Guwahati"],
                            "Flood Level": ["Severe", "High", "Moderate", "Severe", "Moderate"],
                            "Displaced": [23000, 15000, 8000, 12000, 9000],
                            "Rainfall (mm)": [2200, 2100, 1800, 2400, 1900],
                            "Relief Camps": [25, 18, 12, 22, 15]
                        }, use_container_width=True)

                    elif "forest_fire" in msg["image"]:
                        st.markdown("#### 📊 Forest Fire Incidents (Sample)")
                        st.dataframe({
                            "Region": ["Shimla", "Chamba", "Sirmaur", "Kullu", "Mandi"],
                            "Avg Temp (°C)": [35, 34, 36, 33, 32],
                            "Incidents": [45, 30, 25, 40, 38],
                            "High Risk Zones": ["Yes", "Yes", "No", "Yes", "Yes"]
                        }, use_container_width=True)

                    elif "traffic" in msg["image"]:
                        st.markdown("#### 📊 Traffic Congestion Points (Sample)")
                        st.dataframe({
                            "City": ["Delhi", "Mumbai", "Chennai", "Bengaluru", "Hyderabad"],
                            "Peak Congestion (%)": [78, 72, 65, 80, 69],
                            "Delay (min/km)": [6.5, 5.8, 5.2, 7.0, 6.0],
                            "Traffic Zones": ["Ring Rd", "Western Exp", "Anna Salai", "Outer Ring Rd", "Hitec City"]
                        }, use_container_width=True)

        elif msg["type"] == "dynamic_map":
            map_obj, summary = get_osm_map_from_query(msg["query"], msg["tags"])
            if map_obj:
                st.markdown(icon, unsafe_allow_html=True)
                st_data = st_folium(map_obj, width=700, height=500)
                st.markdown(f"<span style='font-size:14px'>{summary}</span>", unsafe_allow_html=True)
            else:
                st.error(summary)

        elif msg["type"] == "question":
            for q in msg["questions"]:
                if st.button(q):
                    handle_user_input(q)
                    st.rerun()

# ---------------- Text Input ------------------
user_input = st.chat_input("Type your question here...")
if user_input:
    handle_user_input(user_input)
    st.rerun()

# ---------------- Voice Input ------------------
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
