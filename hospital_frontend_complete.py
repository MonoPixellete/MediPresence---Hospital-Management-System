"""
MediPresence Frontend - Streamlit Dashboard
Run: streamlit run frontend.py
Backend must be running on http://localhost:8000
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

# Configuration
API_BASE = "http://localhost:8000"
st.set_page_config(page_title="MediPresence", layout="wide", initial_sidebar_state="expanded")

# Global styles
st.markdown(
    """
    <style>
        .med-card {
            padding: 1rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(242, 248, 255, 0.9), rgba(255, 255, 255, 0.95));
            box-shadow: 0 8px 18px rgba(60, 90, 154, 0.08);
            margin-bottom: 1rem;
        }
        .metric-card {
            padding: 0.75rem 1rem;
            border-radius: 14px;
            background-color: #f8faff;
            border: 1px solid rgba(64, 120, 255, 0.08);
            text-align: center;
        }
        .stTabs [role="tablist"] {
            gap: 8px;
        }
        .stTabs [role="tab"] {
            background: #f0f4ff;
            border-radius: 999px;
            padding: 0.5rem 1.2rem;
        }
        .css-1y4p8pa, .stButton>button {
            border-radius: 999px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'full_name' not in st.session_state:
    st.session_state.full_name = None

# Helper functions
def make_request(method, endpoint, data=None, headers=None, params=None):
    """Make API request with error handling"""
    url = f"{API_BASE}{endpoint}"
    if headers is None:
        headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        method = method.upper()
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers, params=params, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            st.error(f"Unsupported method {method}")
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def cached_get(endpoint, ttl_seconds=30):
    """Simple session-state cache for GET requests"""
    now = datetime.utcnow()
    cache_key = f"cache::{endpoint}"
    cache_entry = st.session_state.get(cache_key)
    if cache_entry and cache_entry["expires_at"] > now:
        return cache_entry["data"]
    data = make_request("GET", endpoint)
    st.session_state[cache_key] = {"data": data, "expires_at": now + timedelta(seconds=ttl_seconds)}
    return data

def invalidate_cache(prefix):
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith(prefix)]
    for key in keys_to_remove:
        st.session_state.pop(key, None)

def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.full_name = None
    st.rerun()

def get_status_color(status, activity):
    """Return color based on status and activity"""
    if status == "off-duty":
        return "🔴"
    elif activity == "busy":
        return "🟡"
    elif activity == "idle":
        return "🟠"
    else:
        return "🟢"

# Main App
def main():
    # Check if offline mode
    try:
        response = requests.get(f"{API_BASE}/", timeout=2)
    except:
        st.warning("⚠️ OFFLINE MODE ACTIVE - Backend server not reachable")
    
    # Login/Register Page
    if not st.session_state.token:
        st.title("🏥 MediPresence - Hospital Management System")
        st.markdown("### Real-Time Staff Presence & Patient Tracking")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary"):
                if username and password:
                    result = make_request("POST", "/login", {"username": username, "password": password})
                    if result:
                        st.session_state.token = result["token"]
                        st.session_state.user_role = result["role"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.full_name = result["full_name"]
                        st.success(f"Welcome, {result['full_name']}!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Please enter username and password")
        
        with tab2:
            st.subheader("Register New User")
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_fullname = st.text_input("Full Name", key="reg_fullname")
            reg_role = st.selectbox("Role", ["doctor", "nurse", "receptionist", "staff", "admin"])
            
            if st.button("Register", type="primary"):
                if reg_username and reg_email and reg_password and reg_fullname:
                    result = make_request("POST", "/register", {
                        "username": reg_username,
                        "email": reg_email,
                        "password": reg_password,
                        "full_name": reg_fullname,
                        "role": reg_role
                    })
                    if result:
                        st.success("Registration successful! Please login.")
                else:
                    st.error("Please fill all fields")
    
    else:
        # Logged in - Show Dashboard
        show_dashboard()

def show_dashboard():
    """Main dashboard after login"""
    
    # Sidebar
    with st.sidebar:
        st.title("🏥 MediPresence")
        st.markdown(f"**{st.session_state.full_name}**")
        st.markdown(f"*Role: {st.session_state.user_role.upper()}*")
        st.divider()
        
        # Status updater
        st.subheader("Update Status")
        new_status = st.selectbox("Status", ["on-duty", "off-duty"])
        new_activity = st.selectbox("Activity", ["active", "busy", "idle"])
        new_location = st.text_input("Location", "OPD")
        
        if st.button("Update", type="primary"):
            result = make_request("POST", "/staff/update-status", {
                "status": new_status,
                "activity": new_activity,
                "location": new_location
            })
            if result:
                st.success("Status updated!")
                invalidate_cache("cache::/staff/presence")
        
        st.divider()
        if st.button("🚪 Logout", type="secondary"):
            logout()
    
    # Main Content
    role = st.session_state.user_role
    
    if role == "admin":
        show_admin_dashboard()
    elif role == "doctor":
        show_doctor_dashboard()
    elif role == "nurse":
        show_nurse_dashboard()
    elif role == "receptionist":
        show_receptionist_dashboard()
    else:
        show_staff_dashboard()

def show_admin_dashboard():
    """Admin dashboard with full access"""
    st.title("👨‍💼 Admin Dashboard")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Live Status", "🚨 Alerts", "✅ Tasks", "👥 Patients", "📋 Audit Logs"])
    
    with tab1:
        st.subheader("Staff Live Status")
        if st.button("🔄 Refresh", key="refresh_status"):
            invalidate_cache("cache::/staff/presence")
            st.rerun()
        
        staff_data = cached_get("/staff/presence")
        if staff_data:
            df = pd.DataFrame(staff_data)
            
            # Display in grid
            cols = st.columns(3)
            for idx, row in df.iterrows():
                col = cols[idx % 3]
                with col:
                    status_emoji = get_status_color(row['status'], row['activity'])
                    with st.container(border=True):
                        st.markdown(f"### {status_emoji} {row['full_name']}")
                        st.markdown(f"**Role:** {row['role']}")
                        st.markdown(f"**Status:** {row['status']}")
                        st.markdown(f"**Activity:** {row['activity']}")
                        st.markdown(f"**Location:** {row['location']}")
                        st.markdown(f"**Patients:** {row['assigned_patients']}")
                        if row['last_active']:
                            st.caption(f"Last active: {row['last_active'][:19]}")
            
            # Summary stats
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Staff", len(df))
            with col2:
                on_duty = len(df[df['status'] == 'on-duty'])
                st.metric("On Duty", on_duty)
            with col3:
                active = len(df[df['activity'] == 'active'])
                st.metric("Active", active)
            with col4:
                busy = len(df[df['activity'] == 'busy'])
                st.metric("Busy", busy)
    
    with tab2:
        st.subheader("🚨 Emergency Alerts")
        if st.button("🔄 Refresh", key="refresh_alerts"):
            invalidate_cache("cache::/alerts")
            st.rerun()
        
        alerts = cached_get("/alerts")
        if alerts:
            for alert in alerts:
                priority_color = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(alert['priority'], "⚪")
                
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### {priority_color} {alert['alert_type'].upper()}")
                        st.write(alert['message'])
                        st.caption(f"Created: {alert['created_at'][:19]}")
                    with col2:
                        if st.button("✓ Acknowledge", key=f"ack_{alert['id']}"):
                            result = make_request("POST", f"/alerts/{alert['id']}/acknowledge")
                            if result:
                                st.success("Acknowledged!")
                                invalidate_cache("cache::/alerts")
                                st.rerun()
        else:
            st.success("✅ No active alerts")
    
    with tab3:
        st.subheader("✅ Task Management")
        
        # Create new task
        with st.expander("➕ Create New Task"):
            task_title = st.text_input("Task Title")
            task_desc = st.text_area("Description")
            
            # Get staff list
            staff_data = cached_get("/staff/presence")
            if staff_data:
                staff_options = {s['full_name']: s['user_id'] for s in staff_data}
                assigned_to = st.selectbox("Assign To", list(staff_options.keys()))
                priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
                deadline = st.date_input("Deadline", datetime.now() + timedelta(days=1))
                
                if st.button("Create Task", type="primary"):
                    if task_title:
                        result = make_request("POST", "/tasks", {
                            "title": task_title,
                            "description": task_desc,
                            "assigned_to": staff_options[assigned_to],
                            "priority": priority,
                            "deadline": deadline.isoformat() + "T00:00:00"
                        })
                        if result:
                            st.success("Task created!")
                            invalidate_cache("cache::/tasks")
                            st.rerun()
        
        # Display tasks
        st.divider()
        tasks = cached_get("/tasks")
        if tasks:
            for task in tasks:
                priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(task['priority'], "⚪")
                status_emoji = {"pending": "⏳", "in-progress": "🔄", "completed": "✅"}.get(task['status'], "⚪")
                
                with st.container(border=True):
                    st.markdown(f"### {status_emoji} {task['title']} {priority_emoji}")
                    st.write(task['description'])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Priority: {task['priority']}")
                    with col2:
                        st.caption(f"Status: {task['status']}")
                    with col3:
                        st.caption(f"Deadline: {task['deadline'][:10]}")
        else:
            st.info("No tasks found")
    
    with tab4:
        st.subheader("👥 Patient Management")
        
        # Add new patient
        with st.expander("➕ Register New Patient"):
            pat_name = st.text_input("Patient Name")
            col1, col2 = st.columns(2)
            with col1:
                pat_age = st.number_input("Age", min_value=0, max_value=120, value=30)
            with col2:
                pat_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
            pat_illness = st.text_area("Illness/Condition")
            pat_room = st.text_input("Room Number")
            
            staff_data = cached_get("/staff/presence")
            if staff_data:
                doctors = {s['full_name']: s['user_id'] for s in staff_data if s['role'] == 'doctor'}
                nurses = {s['full_name']: s['user_id'] for s in staff_data if s['role'] == 'nurse'}
                
                col1, col2 = st.columns(2)
                with col1:
                    if doctors:
                        assigned_doctor = st.selectbox("Assigned Doctor", list(doctors.keys()))
                    else:
                        st.warning("No doctors available")
                        assigned_doctor = None
                with col2:
                    if nurses:
                        assigned_nurse = st.selectbox("Assigned Nurse", list(nurses.keys()))
                    else:
                        st.warning("No nurses available")
                        assigned_nurse = None
                
                if st.button("Register Patient", type="primary"):
                    if pat_name and doctors and nurses and assigned_doctor and assigned_nurse:
                        result = make_request("POST", "/patients", {
                            "name": pat_name,
                            "age": int(pat_age),
                            "gender": pat_gender,
                            "illness": pat_illness,
                            "room_number": pat_room,
                            "assigned_doctor_id": doctors[assigned_doctor],
                            "assigned_nurse_id": nurses[assigned_nurse]
                        })
                        if result:
                            st.success("Patient registered!")
                            invalidate_cache("cache::/patients")
                            invalidate_cache("cache::/staff/presence")
                            st.rerun()
                    else:
                        st.error("Please fill all fields and ensure staff are available")
        
        # Display patients
        st.divider()
        patients = cached_get("/patients")
        if patients:
            df = pd.DataFrame(patients)
            st.dataframe(df[['id', 'name', 'age', 'gender', 'room_number', 'illness', 'status']], use_container_width=True)
        else:
            st.info("No patients registered")
    
    with tab5:
        st.subheader("📋 Audit Logs")
        if st.button("🔄 Refresh", key="refresh_logs"):
            st.rerun()
        
        logs = cached_get("/audit-logs")
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df[['id', 'user_id', 'action', 'details', 'created_at']], use_container_width=True)
        else:
            st.info("No audit logs")

def show_doctor_dashboard():
    """Doctor dashboard"""
    st.title("👨‍⚕️ Doctor Dashboard")
    
    patients = cached_get("/patients") or []
    my_patients = [p for p in patients if p['assigned_doctor_id'] == st.session_state.user_id]
    
    tab1, tab2, tab3 = st.tabs(["👥 My Patients", "🩺 Clinical Workflow", "✅ My Tasks"])
    
    with tab1:
        st.subheader("Assigned Patients")
        if my_patients:
            cols = st.columns(2)
            for idx, patient in enumerate(my_patients):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"<div class='med-card'><h4>🏥 {patient['name']}</h4></div>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Age", patient['age'])
                        with col2:
                            st.metric("Room", patient['room_number'])
                        with col3:
                            st.metric("Status", patient.get('status', 'admitted').title())
                        st.caption(f"Admitted: {patient['admitted_at'][:10]} • Condition: {patient['illness']}")
        else:
            st.info("No patients assigned yet.")
    
    with tab2:
        st.subheader("Patient Clinical Workflow")
        if not my_patients:
            st.info("Assign patients to access clinical workflows.")
        else:
            patient_options = {f"{p['name']} (Room {p['room_number']})": p for p in my_patients}
            selected_label = st.selectbox("Select a patient", list(patient_options.keys()))
            patient = patient_options[selected_label]
            
            meds = cached_get(f"/patients/{patient['id']}/medications") or []
            vitals = cached_get(f"/patients/{patient['id']}/vitals") or []
            care_plan = cached_get(f"/patients/{patient['id']}/care-plan") or []
            
            with st.container():
                st.markdown(f"<div class='med-card'><h4>🧑‍⚕️ Care Summary • {patient['name']}</h4></div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    upcoming = next((m for m in meds if m['next_dose_time']), None)
                    dose_time = datetime.fromisoformat(upcoming['next_dose_time']) if upcoming and upcoming['next_dose_time'] else None
                    st.metric("Next Medication",
                              upcoming['medication_name'] if upcoming else "None",
                              (dose_time.strftime("%H:%M") if dose_time else ""))
                with col2:
                    latest_vital = vitals[0] if vitals else None
                    st.metric("Latest Vitals",
                              f"{latest_vital['temperature']}°F" if latest_vital and latest_vital['temperature'] else "—",
                              latest_vital['recorded_at'][11:16] if latest_vital else "")
                with col3:
                    open_steps = len([s for s in care_plan if s['status'] != "completed"])
                    st.metric("Active Plan Steps", open_steps)
            
            st.markdown("#### ➕ Add Clinical Actions")
            colA, colB = st.columns(2)
            with colA:
                with st.form(f"med_form_{patient['id']}"):
                    st.markdown("Schedule Medication")
                    med_name = st.text_input("Medication")
                    med_dose = st.text_input("Dosage / Instructions")
                    med_route = st.selectbox("Route", ["Oral", "IV", "IM", "Subcutaneous", "Other"], index=0)
                    med_frequency = st.number_input("Frequency (hours)", min_value=1, max_value=168, value=8)
                    med_start = st.datetime_input("Start time", datetime.utcnow())
                    med_assigned_nurse = st.number_input("Assign Nurse (ID)", min_value=0, value=0, help="Optional: nurse user ID")
                    submitted = st.form_submit_button("Schedule")
                    if submitted and med_name and med_dose:
                        payload = {
                            "medication_name": med_name,
                            "dosage": med_dose,
                            "route": med_route.lower(),
                            "frequency_hours": int(med_frequency),
                            "start_time": med_start.isoformat(),
                            "assigned_nurse_id": int(med_assigned_nurse) if med_assigned_nurse else None
                        }
                        result = make_request("POST", f"/patients/{patient['id']}/medications", payload)
                        if result:
                            st.success("Medication scheduled.")
                            invalidate_cache(f"cache::/patients/{patient['id']}/medications")
                            st.rerun()
            with colB:
                with st.form(f"care_form_{patient['id']}"):
                    st.markdown("Add Care Plan Step")
                    step_title = st.text_input("Step Title")
                    step_desc = st.text_area("Details", height=120)
                    step_due = st.datetime_input("Due by", datetime.utcnow() + timedelta(hours=4))
                    step_assignee = st.number_input("Assign To (User ID)", min_value=0, value=0, help="Optional clinical staff user ID")
                    submitted = st.form_submit_button("Add Step")
                    if submitted and step_title:
                        payload = {
                            "title": step_title,
                            "description": step_desc,
                            "due_time": step_due.isoformat(),
                            "assigned_to": int(step_assignee) if step_assignee else None
                        }
                        result = make_request("POST", f"/patients/{patient['id']}/care-plan", payload)
                        if result:
                            st.success("Care plan step created.")
                            invalidate_cache(f"cache::/patients/{patient['id']}/care-plan")
                            st.rerun()
            
            st.markdown("#### 📋 Active Care Plan")
            if care_plan:
                for step in care_plan:
                    badge = {"pending": "⏳", "in-progress": "🔄", "completed": "✅"}.get(step['status'], "•")
                    with st.container():
                        with st.expander(f"{badge} {step['title']}"):
                            st.write(step.get("description") or "No description provided.")
                            st.caption(f"Due: {step['due_time'][:16] if step['due_time'] else '—'} | Status: {step['status']}")
                            if step['status'] != "completed":
                                if st.button("Mark completed", key=f"complete_step_{step['id']}"):
                                    result = make_request("POST", f"/care-plan/{step['id']}/status", {"status": "completed"})
                                    if result:
                                        st.success("Step completed.")
                                        invalidate_cache(f"cache::/patients/{patient['id']}/care-plan")
                                        st.rerun()
            else:
                st.info("No care plan steps yet.")
            
            st.markdown("#### 💊 Medication Schedule")
            if meds:
                for med in meds:
                    with st.container(border=True):
                        st.markdown(f"**{med['medication_name']}** — {med['dosage']}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"Route: {med.get('route', 'n/a')}")
                        with col2:
                            next_time = med['next_dose_time'][:16] if med['next_dose_time'] else "—"
                            st.caption(f"Next dose: {next_time}")
                        with col3:
                            st.caption(f"Frequency: every {med['frequency_hours']}h")
                        if st.button("Mark dose administered", key=f"administer_{med['id']}"):
                            result = make_request("POST", f"/medications/{med['id']}/mark-administered", {})
                            if result:
                                st.success("Dose recorded.")
                                invalidate_cache(f"cache::/patients/{patient['id']}/medications")
                                st.rerun()
            else:
                st.info("No medications scheduled yet.")
            
            st.markdown("#### 📈 Recent Vitals")
            if vitals:
                vitals_df = pd.DataFrame(vitals)
                vitals_df['recorded_at'] = pd.to_datetime(vitals_df['recorded_at'])
                chart_df = vitals_df[['recorded_at', 'temperature', 'pulse', 'oxygen_saturation']].set_index('recorded_at')
                st.line_chart(chart_df)
            else:
                st.info("Vitals will appear here once recorded.")
    
    with tab3:
        st.subheader("My Tasks")
        tasks = cached_get("/tasks") or []
        my_tasks = [t for t in tasks if t.get('assigned_to') == st.session_state.user_id or st.session_state.user_role == "admin"]
        if my_tasks:
            for task in my_tasks:
                priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(task['priority'], "⚪")
                status_emoji = {"pending": "⏳", "in-progress": "🔄", "completed": "✅"}.get(task['status'], "⚪")
                with st.container(border=True):
                    st.markdown(f"### {status_emoji} {priority_emoji} {task['title']}")
                    st.write(task['description'])
                    st.caption(f"Deadline: {task['deadline'][:10]} | Status: {task['status']}")
        else:
            st.info("No tasks assigned right now.")

def show_nurse_dashboard():
    """Nurse dashboard"""
    st.title("👩‍⚕️ Nurse Dashboard")
    
    patients = cached_get("/patients") or []
    my_patients = [p for p in patients if p['assigned_nurse_id'] == st.session_state.user_id]
    
    tab1, tab2, tab3 = st.tabs(["👥 My Patients", "🩺 Clinical Workflow", "✅ My Tasks"])
    
    with tab1:
        st.subheader("Assigned Patients")
        if my_patients:
            for patient in my_patients:
                with st.container(border=True):
                    st.markdown(f"### 🏥 {patient['name']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Room:** {patient['room_number']}")
                    with col2:
                        st.write(f"**Condition:** {patient['illness']}")
                    
                    with st.expander("📊 Enter Vitals", expanded=False):
                        with st.form(f"vitals_form_{patient['id']}"):
                            temp = st.number_input("Temperature (°F)", min_value=90.0, max_value=110.0, value=98.6, key=f"temp_{patient['id']}")
                            bp = st.text_input("Blood Pressure", placeholder="120/80", key=f"bp_{patient['id']}")
                            pulse = st.number_input("Pulse (bpm)", min_value=40, max_value=200, value=75, key=f"pulse_{patient['id']}")
                            resp = st.number_input("Respiration Rate", min_value=6, max_value=60, value=16, key=f"resp_{patient['id']}")
                            spo2 = st.number_input("SpO₂ (%)", min_value=70, max_value=100, value=98, key=f"spo2_{patient['id']}")
                            notes = st.text_area("Notes", key=f"note_{patient['id']}")
                            submitted = st.form_submit_button("Save Vitals")
                            if submitted:
                                payload = {
                                    "temperature": float(temp),
                                    "blood_pressure": bp,
                                    "pulse": int(pulse),
                                    "respiration_rate": int(resp),
                                    "oxygen_saturation": float(spo2),
                                    "notes": notes
                                }
                                result = make_request("POST", f"/patients/{patient['id']}/vitals", payload)
                                if result:
                                    st.success("Vitals recorded.")
                                    invalidate_cache(f"cache::/patients/{patient['id']}/vitals")
                                    st.rerun()
        else:
            st.info("No patients assigned")
    
    with tab2:
        st.subheader("Clinical Workflow")
        if not my_patients:
            st.info("No assigned patients yet.")
        else:
            patient_options = {f"{p['name']} • Room {p['room_number']}": p for p in my_patients}
            selected = st.selectbox("Choose patient", list(patient_options.keys()), key="nurse_patient_select")
            patient = patient_options[selected]
            
            meds = cached_get(f"/patients/{patient['id']}/medications") or []
            vitals = cached_get(f"/patients/{patient['id']}/vitals") or []
            care_plan = cached_get(f"/patients/{patient['id']}/care-plan") or []
            
            col1, col2, col3 = st.columns(3)
            with col1:
                upcoming = next((m for m in meds if m['next_dose_time']), None)
                label = upcoming['medication_name'] if upcoming else "—"
                st.metric("Next medication", label)
            with col2:
                latest = vitals[0] if vitals else None
                st.metric("Latest pulse", latest['pulse'] if latest and latest['pulse'] else "—")
            with col3:
                open_steps = len([s for s in care_plan if s['status'] != "completed"])
                st.metric("Open care steps", open_steps)
            
            st.markdown("#### 💊 Medication administration")
            for med in meds:
                with st.container(border=True):
                    st.markdown(f"**{med['medication_name']}** ({med['dosage']})")
                    st.caption(f"Next dose: {med['next_dose_time'][:16] if med['next_dose_time'] else '—'} • Frequency: every {med['frequency_hours']}h")
                    if st.button("Dose given", key=f"nurse_admin_{med['id']}"):
                        result = make_request("POST", f"/medications/{med['id']}/mark-administered", {})
                        if result:
                            st.success("Administration logged.")
                            invalidate_cache(f"cache::/patients/{patient['id']}/medications")
                            st.rerun()
            
            st.markdown("#### 📋 Care plan follow-up")
            for step in care_plan:
                if step['status'] == "completed":
                    continue
                with st.container(border=True):
                    st.markdown(f"**{step['title']}**")
                    st.write(step.get("description") or "")
                    st.caption(f"Due: {step['due_time'][:16] if step['due_time'] else '—'}")
                    if st.button("Mark as in-progress", key=f"nurse_progress_{step['id']}"):
                        result = make_request("POST", f"/care-plan/{step['id']}/status", {"status": "in-progress"})
                        if result:
                            st.success("Status updated.")
                            invalidate_cache(f"cache::/patients/{patient['id']}/care-plan")
                            st.rerun()
    
    with tab3:
        st.subheader("My Tasks")
        tasks = cached_get("/tasks")
        if tasks:
            for task in tasks:
                priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(task['priority'], "⚪")
                status_emoji = {"pending": "⏳", "in-progress": "🔄", "completed": "✅"}.get(task['status'], "⚪")
                with st.container(border=True):
                    st.markdown(f"### {status_emoji} {priority_emoji} {task['title']}")
                    st.write(task['description'])
                    st.caption(f"Deadline: {task['deadline'][:10]} | Status: {task['status']}")
        else:
            st.info("No tasks assigned")

def show_receptionist_dashboard():
    """Receptionist dashboard"""
    st.title("📝 Receptionist Dashboard")
    
    st.subheader("Patient Registration")
    
    with st.form("patient_form"):
        pat_name = st.text_input("Patient Name")
        col1, col2 = st.columns(2)
        with col1:
            pat_age = st.number_input("Age", min_value=0, max_value=120, value=30)
        with col2:
            pat_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        pat_illness = st.text_area("Chief Complaint")
        pat_room = st.text_input("Room Number")
        
        staff_data = cached_get("/staff/presence")
        doctors = {s['full_name']: s['user_id'] for s in (staff_data or []) if s['role'] == 'doctor'}
        nurses = {s['full_name']: s['user_id'] for s in (staff_data or []) if s['role'] == 'nurse'}
        
        col1, col2 = st.columns(2)
        with col1:
            if doctors:
                assigned_doctor = st.selectbox("Assigned Doctor", list(doctors.keys()))
            else:
                st.warning("No doctors available")
                assigned_doctor = None
        with col2:
            if nurses:
                assigned_nurse = st.selectbox("Assigned Nurse", list(nurses.keys()))
            else:
                st.warning("No nurses available")
                assigned_nurse = None
        
        submitted = st.form_submit_button("Register Patient", type="primary")
        
        if submitted and pat_name and doctors and nurses and assigned_doctor and assigned_nurse:
            result = make_request("POST", "/patients", {
                "name": pat_name,
                "age": int(pat_age),
                "gender": pat_gender,
                "illness": pat_illness,
                "room_number": pat_room,
                "assigned_doctor_id": doctors[assigned_doctor],
                "assigned_nurse_id": nurses[assigned_nurse]
            })
            if result:
                st.success(f"Patient {pat_name} registered successfully!")
                invalidate_cache("cache::/patients")
                invalidate_cache("cache::/staff/presence")
                st.rerun()
    
    st.divider()
    st.subheader("Recent Patients")
    patients = cached_get("/patients")
    if patients:
        df = pd.DataFrame(patients)
        st.dataframe(df[['id', 'name', 'age', 'room_number', 'admitted_at']], use_container_width=True)
    else:
        st.info("No patients registered yet")

def show_staff_dashboard():
    """General staff dashboard"""
    st.title("👤 Staff Dashboard")
    
    st.subheader("My Tasks")
    tasks = cached_get("/tasks")
    if tasks:
        for task in tasks:
            priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(task['priority'], "⚪")
            status_emoji = {"pending": "⏳", "in-progress": "🔄", "completed": "✅"}.get(task['status'], "⚪")
            with st.container(border=True):
                st.markdown(f"### {status_emoji} {priority_emoji} {task['title']}")
                st.write(task['description'])
                st.caption(f"Deadline: {task['deadline'][:10]} | Status: {task['status']}")
    else:
        st.info("No tasks assigned")
    
    st.divider()
    st.subheader("Staff Status Overview")
    staff_data = make_request("GET", "/staff/presence")
    if staff_data:
        df = pd.DataFrame(staff_data)
        st.dataframe(df[['full_name', 'role', 'status', 'activity', 'location']], use_container_width=True)

if __name__ == "__main__":
    main()
