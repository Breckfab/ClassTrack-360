import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO CSS MODERNO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button { 
        background-image: linear-gradient(to right, #2563eb, #7c3aed);
        color: white; border-radius: 8px; border: none; font-weight: 500;
        padding: 0.6rem 2rem; transition: 0.3s; width: 100%;
    }
    .card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 15px;
    }
    .logo-text {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(to right, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE (breckfab@gmail.com) ---
@st.cache_resource
def init_connection():
    # Usamos tus credenciales de la Imagen 02
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- PANTALLA DE LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Reemplazo del logo roto por el diseño visual sofisticado
        st.markdown("""
            <div style='text-align: center;'>
                <svg viewBox="0 0 100 60" xmlns="http://www.w3.org/2000/svg" width="150">
                    <path d="M10 30 Q 50 0 90 30 Q 50 60 10 30" fill="none" stroke="#7c3aed" stroke-width="2"/>
                    <circle cx="50" cy="30" r="12" fill="#2563eb" fill-opacity="0.3" stroke="#2563eb" stroke-width="2"/>
                    <text x="50" y="35" font-family="Arial" font-size="8" fill="white" text-anchor="middle">360</text>
                </svg>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            u = st.text_input("Usuario (Email)")
            p = st.text_input("Contraseña", type="password")
            if st.button("Acceder al Sistema"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: st.error("Credenciales no válidas.")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- PANEL INTERNO (PROFE / ADMIN) ---
    user = st.session_state.user
    st.sidebar.markdown("### ClassTrack 360")
    st.sidebar.write(f"Conectado: {user['email']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()
    
    st.title("📑 Gestión Académica")
    # Aquí continúa tu lógica de pestañas para Cambridge/Daguerre
