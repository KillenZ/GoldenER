import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math
import urllib.request
import json
from datetime import datetime
import copy

# =====================================================================
# 1. FULL-SCREEN APP CONFIG & ANIMATED CSS
# =====================================================================
st.set_page_config(
    page_title="VitalPath",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    .stApp {
        background-color: #090d16;
        color: #e2e8f0;
    }
    
    /* Smooth 1.5s Glide-In Animation for Splash Screen */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(35px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animated-splash {
        animation: fadeInUp 1.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .app-topbar {
        background: #111827;
        border: 1px solid #1f2937;
        border-bottom: 2px solid #ef4444;
        padding: 10px 20px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .status-pill {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid #10b981;
        padding: 3px 10px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 700;
    }
    .alert-pill {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 3px 10px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #1e293b;
        padding: 12px 16px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. HOSPITAL DATABASE & SESSION STATE
# =====================================================================
DEFAULT_HOSPITALS = [
    {"id": 1, "name": "Jag Pravesh Chandra Hospital (Shastri Park)", "lat": 28.6765, "lon": 77.2629, "icu_beds": 0, "ventilators": 0, "traffic_factor": 1.2, "blood": {"O-": 0, "O+": 4, "A+": 5, "B+": 3, "AB+": 2}},
    {"id": 2, "name": "Sushruta Trauma Centre (Civil Lines)", "lat": 28.6815, "lon": 77.2248, "icu_beds": 0, "ventilators": 1, "traffic_factor": 1.3, "blood": {"O-": 1, "O+": 3, "A+": 2, "B+": 4, "AB+": 1}},
    {"id": 3, "name": "Sant Parmanand Hospital (Civil Lines)", "lat": 28.6795, "lon": 77.2225, "icu_beds": 2, "ventilators": 2, "traffic_factor": 1.1, "blood": {"O-": 3, "O+": 6, "A+": 5, "B+": 4, "AB+": 3}},
    {"id": 4, "name": "Aruna Asaf Ali Govt. Hospital (Rajpur Rd)", "lat": 28.6705, "lon": 77.2215, "icu_beds": 2, "ventilators": 0, "traffic_factor": 1.4, "blood": {"O-": 0, "O+": 4, "A+": 3, "B+": 2, "AB+": 1}},
    {"id": 5, "name": "St. Stephen's Hospital (Tis Hazari)", "lat": 28.6651, "lon": 77.2145, "icu_beds": 5, "ventilators": 4, "traffic_factor": 1.1, "blood": {"O-": 4, "O+": 8, "A+": 6, "B+": 5, "AB+": 4}},
    {"id": 6, "name": "Tirath Ram Shah Hospital (Civil Lines)", "lat": 28.6732, "lon": 77.2185, "icu_beds": 3, "ventilators": 2, "traffic_factor": 1.2, "blood": {"O-": 2, "O+": 5, "A+": 4, "B+": 3, "AB+": 2}},
    {"id": 7, "name": "Swami Dayanand Hospital (Shahdara)", "lat": 28.6792, "lon": 77.2982, "icu_beds": 1, "ventilators": 1, "traffic_factor": 1.3, "blood": {"O-": 0, "O+": 3, "A+": 3, "B+": 2, "AB+": 1}},
    {"id": 8, "name": "Guru Teg Bahadur (GTB) Hospital (Dilshad Garden)", "lat": 28.6840, "lon": 77.3090, "icu_beds": 8, "ventilators": 6, "traffic_factor": 1.1, "blood": {"O-": 5, "O+": 10, "A+": 7, "B+": 6, "AB+": 4}},
    {"id": 9, "name": "Lok Nayak Hospital - LNJP (Delhi Gate)", "lat": 28.6385, "lon": 77.2372, "icu_beds": 7, "ventilators": 5, "traffic_factor": 1.2, "blood": {"O-": 4, "O+": 9, "A+": 6, "B+": 5, "AB+": 3}},
    {"id": 10, "name": "Rajiv Gandhi Super Speciality (Tahirpur)", "lat": 28.6895, "lon": 77.3168, "icu_beds": 5, "ventilators": 4, "traffic_factor": 1.2, "blood": {"O-": 3, "O+": 7, "A+": 5, "B+": 4, "AB+": 3}},
]

if "hospitals" not in st.session_state:
    st.session_state.hospitals = copy.deepcopy(DEFAULT_HOSPITALS)

if "dispatch_log" not in st.session_state:
    st.session_state.dispatch_log = []

if "app_started" not in st.session_state:
    st.session_state.app_started = False

# =====================================================================
# 3. ANIMATED SPLASH SCREEN (INITIAL OPENING SCREEN)
# =====================================================================
if not st.session_state.app_started:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_a, col_center, col_b = st.columns([1, 2.5, 1])
    
    with col_center:
        st.markdown('<div class="animated-splash">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color: #f87171;'>🚑 GoldenHour ER Router</h1>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #94a3b8;'>Live City Triage & Smart Ambulance Dispatch OS</h4>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("""
            **The Emergency Problem:**
            Ambulances take critical trauma patients to the closest hospital on the map, only to discover the ICU or ventilator is full—wasting **40 critical minutes** transferring them.
            
            **Our AI Solution:**
            A real-time dispatch dashboard tracking ICU beds, ventilators, and blood banks across **10 hospitals near ADGIPS (Shastri Park)**, routing incoming ambulances to the **fastest equipped ER**.
            """)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 LAUNCH 112 DISPATCH CONSOLE", type="primary", use_container_width=True):
                st.session_state.app_started = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# 4. ROUTING & OSRM ENGINE
# =====================================================================
def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

def calculate_eta_minutes(distance_km, traffic_factor):
    return max(2, round((distance_km * 1.5) * traffic_factor))

@st.cache_data(show_spinner=False)
def get_street_route(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'GoldenHourApp/1.0'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
            data = json.loads(response.read().decode())
            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[c[1], c[0]] for c in coords]
    except Exception:
        return [[lat1, lon1], [lat2, lon2]]

# =====================================================================
# 5. POP-UP MODAL WINDOW FOR DISPATCH
# =====================================================================
@st.dialog("🚨 Confirm Emergency Dispatch & ICU Lock")
def open_dispatch_modal(amb_id, patient_condition, hospital, need_icu, need_vent, blood_needed, time_saved):
    st.markdown(f"### 🚑 Unit `{amb_id}` ➔ **{hospital['name']}**")
    st.caption("Locking this resource immediately reserves the bed on the city grid.")
    
    col1, col2 = st.columns(2)
    col1.metric("Estimated Arrival", f"{hospital['eta_mins']} Mins", f"{hospital['distance_km']} km via Green Corridor")
    col2.metric("Transfer Time Saved", f"{time_saved} Mins", "Golden Hour Protected")

    st.markdown("**Resources to Lock at Destination ER:**")
    st.write(f"- 🛏️ **ICU Bed:** {'Yes (1 Bed Reserved)' if need_icu else 'Not Required'}")
    st.write(f"- 🫁 **Ventilator:** {'Yes (1 Unit Reserved)' if need_vent else 'Not Required'}")
    st.write(f"- 🩸 **Blood Bank:** {f'1 Unit of {blood_needed} Reserved' if blood_needed != 'None' else 'Not Required'}")

    if st.button("✅ TRANSMIT PRE-ARRIVAL TICKET & LOCK BED", type="primary", use_container_width=True):
        for h in st.session_state.hospitals:
            if h["id"] == hospital["id"]:
                if need_icu and h["icu_beds"] > 0: h["icu_beds"] -= 1
                if need_vent and h["ventilators"] > 0: h["ventilators"] -= 1
                if blood_needed != "None" and h["blood"].get(blood_needed, 0) > 0: h["blood"][blood_needed] -= 1
        
        st.session_state.dispatch_log.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "ambulance": amb_id,
            "condition": patient_condition,
            "destination": hospital["name"],
            "eta": f"{hospital['eta_mins']} mins",
            "saved": f"{time_saved} mins"
        })
        st.rerun()

# =====================================================================
# 6. SIDEBAR NAVIGATION
# =====================================================================
with st.sidebar:
    st.markdown("### ⚡ **GoldenHour CAD OS**")
    st.caption("Sector: Shastri Park & North-East Delhi")
    st.markdown("---")
    
    app_screen = st.radio(
        "SYSTEM VIEWS",
        [
            "🛰️ Live CAD Dispatch Console",
            "🏥 Hospital Capacity Matrix",
            f"📋 Active Dispatch Tickets ({len(st.session_state.dispatch_log)})"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("##### 📻 Live Sector Status")
    total_icu = sum(h["icu_beds"] for h in st.session_state.hospitals)
    total_vent = sum(h["ventilators"] for h in st.session_state.hospitals)
    
    sb1, sb2 = st.columns(2)
    sb1.metric("ICU Beds", total_icu)
    sb2.metric("Ventilators", total_vent)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset App & Database", use_container_width=True):
        st.session_state.hospitals = copy.deepcopy(DEFAULT_HOSPITALS)
        st.session_state.dispatch_log = []
        st.session_state.app_started = False
        st.rerun()

# =====================================================================
# 7. TOP APPLICATION STATUS BAR
# =====================================================================
st.markdown(f"""
<div class="app-topbar">
    <div>
        <strong style="font-size: 18px; color: white;">🚑 GOLDENHOUR ER ROUTER</strong>
        <span style="color: #64748b; margin-left: 10px; font-size: 13px;">CAD 112 DISPATCH SYSTEM</span>
    </div>
    <div>
        <span class="status-pill">● OSRM STREET ROUTING ONLINE</span>
        <span class="alert-pill" style="margin-left: 8px;">ACTIVE DISPATCHES: {len(st.session_state.dispatch_log)}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# VIEW 1: LIVE CAD DISPATCH CONSOLE
# =====================================================================
if app_screen.startswith("🛰️"):
    col_input, col_map, col_verdict = st.columns([1.05, 1.9, 1.05])

    with col_input:
        with st.container(border=True):
            st.markdown("#### 🚨 Incoming 112 Call")
            amb_id = st.selectbox("Ambulance Unit ID", ["DL-112-ALPHA (ADGIPS Gate)", "DL-112-BRAVO (ISBT)", "DL-112-CHARLIE (Metro)"])
            
            if "ALPHA" in amb_id:
                amb_lat, amb_lon = 28.6776, 77.2611
                condition = "Severe Multi-Trauma"
                def_spo2, def_icu, def_vent, def_blood = 82, True, True, "O-"
            elif "BRAVO" in amb_id:
                amb_lat, amb_lon = 28.6695, 77.2285
                condition = "Acute Cardiac Arrest"
                def_spo2, def_icu, def_vent, def_blood = 85, True, True, "None"
            else:
                amb_lat, amb_lon = 28.6702, 77.2515
                condition = "Moderate Blood Loss"
                def_spo2, def_icu, def_vent, def_blood = 96, False, False, "O+"

            st.caption(f"📍 **GPS Lock:** `{amb_lat}, {amb_lon}`")
            
            spo2 = st.slider("SpO2 Oxygen (%)", 60, 100, def_spo2)
            c1, c2 = st.columns(2)
            need_icu = c1.toggle("ICU Bed", value=def_icu)
            need_vent = c2.toggle("Ventilator", value=(def_vent or spo2 < 88))
            blood_needed = st.selectbox("Blood Type", ["None", "O-", "O+", "A+", "B+", "AB+"], index=["None", "O-", "O+", "A+", "B+", "AB+"].index(def_blood))

    evaluated_hospitals = []
    for h in st.session_state.hospitals:
        dist = calculate_distance_km(amb_lat, amb_lon, h["lat"], h["lon"])
        eta = calculate_eta_minutes(dist, h["traffic_factor"])
        has_icu = (h["icu_beds"] > 0) if need_icu else True
        has_vent = (h["ventilators"] > 0) if need_vent else True
        has_blood = (h["blood"].get(blood_needed, 99) > 0) if blood_needed != "None" else True
        is_equipped = has_icu and has_vent and has_blood

        missing = []
        if not has_icu: missing.append("0 ICU")
        if not has_vent: missing.append("0 Vent")
        if not has_blood: missing.append(f"0 {blood_needed}")

        evaluated_hospitals.append({
            **h,
            "distance_km": dist,
            "eta_mins": eta,
            "is_equipped": is_equipped,
            "status_note": "✅ EQUIPPED" if is_equipped else "❌ " + ", ".join(missing)
        })

    closest_hospital = min(evaluated_hospitals, key=lambda x: x["eta_mins"])
    equipped_hospitals = [h for h in evaluated_hospitals if h["is_equipped"]]
    optimal_hospital = min(equipped_hospitals, key=lambda x: x["eta_mins"]) if equipped_hospitals else None

    naive_time = closest_hospital["eta_mins"] + (40 if not closest_hospital["is_equipped"] else 0)
    time_saved = (naive_time - optimal_hospital["eta_mins"]) if optimal_hospital else 0

    with col_map:
        with st.container(border=True):
            m = folium.Map(location=[amb_lat, amb_lon], zoom_start=13, tiles="OpenStreetMap")

            folium.Circle(
                location=[amb_lat, amb_lon], radius=2000, color="#3b82f6", fill=True, fill_opacity=0.08
            ).add_to(m)

            folium.Marker(
                [amb_lat, amb_lon],
                tooltip=f"🚑 {amb_id}",
                icon=folium.Icon(color="blue", icon="ambulance", prefix="fa")
            ).add_to(m)

            for h in evaluated_hospitals:
                color = "green" if (optimal_hospital and h["id"] == optimal_hospital["id"]) else ("lightgreen" if h["is_equipped"] else "red")
                folium.Marker(
                    [h["lat"], h["lon"]],
                    tooltip=f"{h['name']} ({h['eta_mins']}m) | ICU: {h['icu_beds']} | Vent: {h['ventilators']}",
                    icon=folium.Icon(color=color, icon="plus-sign")
                ).add_to(m)

            if not closest_hospital["is_equipped"]:
                trap_coords = get_street_route(amb_lat, amb_lon, closest_hospital["lat"], closest_hospital["lon"])
                folium.PolyLine(trap_coords, color="#ef4444", weight=4, dash_array="8, 8", tooltip="❌ Closest ER (Missing Equipment)").add_to(m)

            if optimal_hospital:
                opt_coords = get_street_route(amb_lat, amb_lon, optimal_hospital["lat"], optimal_hospital["lon"])
                folium.PolyLine(opt_coords, color="#10b981", weight=6, tooltip="✅ GoldenHour Street Route").add_to(m)

            st_folium(m, width=650, height=440, returned_objects=[])

    with col_verdict:
        with st.container(border=True):
            st.markdown("#### 🧠 Routing Verdict")
            if optimal_hospital:
                if not closest_hospital["is_equipped"]:
                    st.error(f"**BYPASS ALERT:** {closest_hospital['name']} ({closest_hospital['eta_mins']}m) has **{closest_hospital['status_note']}**.")
                else:
                    st.success("**DIRECT ROUTE:** Closest ER is ready!")

                st.metric("🎯 Recommended ER", optimal_hospital["name"][:24], f"{optimal_hospital['eta_mins']} mins ETA ({optimal_hospital['distance_km']} km)")
                st.metric("⏱️ Golden Hour Saved", f"{time_saved} Minutes", "Avoids 40m ICU Transfer Delay" if time_saved > 0 else "No Diversion Needed")

                st.markdown("---")
                st.caption(f"**Target Stock:** 🛏️ {optimal_hospital['icu_beds']} ICU  |  🫁 {optimal_hospital['ventilators']} Vent")

                if st.button("🚀 DISPATCH & LOCK ICU BED", type="primary", use_container_width=True):
                    open_dispatch_modal(amb_id, condition, optimal_hospital, need_icu, need_vent, blood_needed, time_saved)
            else:
                st.warning("🚨 All 10 hospitals lack the selected resources!")

# =====================================================================
# VIEW 2: HOSPITAL CAPACITY MATRIX
# =====================================================================
elif app_screen.startswith("🏥"):
    st.subheader("🏥 Live 10-Hospital Resource Control Matrix")
    st.caption("Manage ICU beds, ventilators, and blood inventory in real time across the North Delhi sector.")
    
    cols = st.columns(2)
    for idx, h in enumerate(st.session_state.hospitals):
        with cols[idx % 2]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{h['name']}**")
                c2.markdown("🟢 **ONLINE**" if h["icu_beds"] > 0 else "🔴 **ICU FULL**")
                
                b1, b2, b3 = st.columns(3)
                new_icu = b1.number_input("ICU Beds", 0, 15, h["icu_beds"], key=f"icu_{h['id']}")
                new_vent = b2.number_input("Ventilators", 0, 15, h["ventilators"], key=f"vent_{h['id']}")
                b3.metric("O- / O+ Blood", f"{h['blood']['O-']} / {h['blood']['O+']}")
                
                if new_icu != h["icu_beds"] or new_vent != h["ventilators"]:
                    h["icu_beds"] = new_icu
                    h["ventilators"] = new_vent
                    st.rerun()

# =====================================================================
# VIEW 3: ACTIVE DISPATCH TICKETS LOG
# =====================================================================
elif app_screen.startswith("📋"):
    st.subheader("📋 Active Ambulance Dispatch Log")
    if not st.session_state.dispatch_log:
        st.info("No active dispatches. Go to **Live CAD Dispatch Console** and click **🚀 DISPATCH & LOCK ICU BED** to record a dispatch ticket!")
    else:
        st.dataframe(pd.DataFrame(st.session_state.dispatch_log), use_container_width=True, hide_index=True)
