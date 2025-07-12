# ------------------- Import Libraries -------------------
import uuid
import re
import streamlit as st
import folium
import speech_recognition as sr
import osmnx as ox
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap

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

# ------------------- Global Hazard Map -------------------
def show_global_hazard_dashboard(focus="all"):
    st.markdown("## 🌐 Hazard Map")

    m = leafmap.Map(center=[24, 87], zoom=5)

    if focus in ["all", "fire"]:
        m.add_wms_layer(
            url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi",
            layers="MODIS_Terra_Thermal_Anomalies_Day",
            name="🔥 Fires (MODIS)",
            format="image/png",
            transparent=True
        )
    if focus in ["all", "flood"]:
        m.add_wms_layer(
            url="https://sedac.ciesin.columbia.edu/geoserver/wms",
            layers="ndh:ndh-flood-hazard-frequency-distribution",
            name="🌊 Flood Hazard",
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

    m.to_streamlit(width=1000, height=600)


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

    for key in friendly_responses:
        if re.fullmatch(rf".*\b{re.escape(key)}\b.*", msg):
            return {"type": "text", "content": friendly_responses[key]}

    for keyword, tags in updated_keywords.items():
        if keyword in msg and " in " in msg:
            return {"type": "dynamic_map", "query": msg, "tags": tags}

    if any(k in msg for k in ["forest fire", "wildfire"]):
        return {"type": "global_hazard_map", "content": info_map["forest_fire"]}
    elif "landslide" in msg:
        return {"type": "global_hazard_map", "content": info_map["landslide"]}
    elif "flood" in msg:
        return {"type": "global_hazard_map", "content": info_map["flood"]}

    elif "global hazard" in msg or ("show" in msg and "hazard" in msg):
        return {"type": "global_hazard_map", "content": info_map["global_hazard"]}

    return {"type": "text", "content": "Hello! 👋 I'm your GIS assistant. Ask me about hazards, POIs, or regions."}

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
            if "flood" in msg["content"].lower():
                show_global_hazard_dashboard("flood")
            elif "landslide" in msg["content"].lower():
                show_global_hazard_dashboard("landslide")
            elif "fire" in msg["content"].lower():
                show_global_hazard_dashboard("fire")
            else:
                show_global_hazard_dashboard("all")
            st.markdown(f"<span style='font-size:14px'>{msg['content']}</span>", unsafe_allow_html=True)

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
