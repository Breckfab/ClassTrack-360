import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# Configuración de estilo y colores modernos
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# Diseño visual vibrante
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button { 
        background-image: linear-gradient(to right, #6366f1, #a855f7);
        color: white; border-radius: 12px; border: none; font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.05); }
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 25px; border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Conexión segura con las llaves que me pasaste
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🚀 ClassTrack 360")

# --- LÓGICA DE LOGIN ---
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    with st.container():
        st.markdown('<div class="card"><h3>🔐 Ingreso al Sistema</h3>', unsafe_allow_html=True)
        email = st.text_input("Usuario (Email)")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", password).execute()
            if res.data:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    user = st.session_state.user
    st.sidebar.markdown(f"### 👤 {user['email']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    # --- PANEL ADMIN ---
    if user['rol'] == 'admin':
        st.header("🛡️ Consola de Administración")
        st.write("Bienvenido Fabian. Aquí podrás gestionar todos los perfiles.")
        # Aquí agregaremos luego la creación de usuarios nuevos
        
    # --- PANEL PROFESOR (Cambridge / Daguerre) ---
    else:
        inst = "Cambridge" if "cambridge" in user['email'] else "Daguerre"
        st.header(f"📊 Panel {inst}")
        
        tab1, tab2, tab3 = st.tabs(["📅 Agenda Diaria", "👥 Alumnos", "🔍 Buscador"])
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            with col1:
                fecha = st.date_input("Día de clase", datetime.date.today())
                st.markdown('<div class="card"><h4>🔔 Pendientes</h4><p>No hay tareas arrastradas.</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.text_area("¿Qué se hizo hoy?")
                st.text_area("Tarea para la próxima")
                st.button("Guardar Registro")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.write("Carga masiva de alumnos (Próximamente)")
