import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO CSS (SOFISTICADO Y PROFESIONAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    
    .stButton>button { 
        background-image: linear-gradient(to right, #2563eb, #7c3aed);
        color: white; border-radius: 10px; border: none; font-weight: 600;
        padding: 0.7rem 2rem; transition: 0.4s; width: 100%;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stButton>button:hover { 
        transform: translateY(-3px); 
        box-shadow: 0px 8px 20px rgba(124, 58, 237, 0.4); 
    }
    
    .card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        padding: 30px; border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .logo-text {
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(to right, #3b82f6, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        margin-top: -10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE (breckfab@gmail.com) ---
@st.cache_resource
def init_connection():
    # Credenciales confirmadas según tu configuración
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- PANTALLA DE LOGIN CON LOGO DETALLADO ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Inyectamos el Ojo 360 Tecnológico con SVG detallado
        st.markdown("""
            <div class="logo-container">
                <svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg" width="180">
                    <defs>
                        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#a855f7;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <path d="M10 40 Q 60 0 110 40 Q 60 80 10 40" fill="none" stroke="url(#grad1)" stroke-width="2.5" />
                    <circle cx="60" cy="40" r="28" fill="none" stroke="#3b82f6" stroke-width="0.5" stroke-dasharray="2,2" />
                    <circle cx="60" cy="40" r="18" fill="rgba(59, 130, 246, 0.1)" stroke="url(#grad1)" stroke-width="2" />
                    <text x="60" y="44" font-family="'Inter', sans-serif" font-weight="800" font-size="10" fill="white" text-anchor="middle">360</text>
                    <circle cx="60" cy="12" r="1.5" fill="#3b82f6" />
                    <circle cx="60" cy="68" r="1.5" fill="#a855f7" />
                </svg>
                <div class="logo-text">ClassTrack 360</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.button("Ingresar al Ecosistema"):
                try:
                    res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado. Verifique sus datos.")
                except Exception as e:
                    st.error("Error de conexión con la base de datos.")
            st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL INTERNO ---
else:
    user = st.session_state.user
    st.sidebar.markdown("<h2 style='text-align: center; color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center;'>{user['email']}</p>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    # VISTA ADMIN
    if user['rol'] == 'admin':
        st.title("🛡️ Consola de Administración")
        st.markdown('<div class="card">Bienvenido Fabián. Las bases de datos están sincronizadas bajo breckfab@gmail.com.</div>', unsafe_allow_html=True)
        
    # VISTA PROFESOR
    else:
        st.title(f"📑 Gestión de Clases")
        tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

        with tabs[2]: # Pestaña de
