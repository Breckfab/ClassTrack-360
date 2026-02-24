import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN Y ESTILO VIBRANTE ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button { 
        background-image: linear-gradient(to right, #4f46e5, #7c3aed);
        color: white; border-radius: 12px; border: none; font-weight: bold;
        padding: 0.6rem 2rem; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 0px 15px rgba(124, 58, 237, 0.4); }
    .card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
    }
    .task-alert { border-left: 5px solid #f59e0b; padding-left: 15px; background: rgba(245, 158, 11, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DE LOGIN ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center;'>🚀 ClassTrack 360</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        u = st.text_input("Usuario (Email)")
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
            if res.data:
                st.session_state.user = res.data[0]
                st.rerun()
            else: st.error("Credenciales incorrectas")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SISTEMA ADENTRO ---
else:
    user = st.session_state.user
    st.sidebar.title("ClassTrack 360")
    st.sidebar.markdown(f"👤 **{user['email']}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    # --- VISTA ADMIN ---
    if user['rol'] == 'admin':
        st.title("🛡️ Consola de Administración")
        tab_u, tab_c = st.tabs(["👥 Usuarios", "📥 Carga Masiva"])
        
        with tab_u:
            st.markdown('<div class="card"><h4>Profesores Activos</h4></div>', unsafe_allow_html=True)
            profs = supabase.table("usuarios").select("email, rol").execute()
            st.table(profs.data)
            
        with tab_c:
            st.write("Subí un Excel con: apellido, nombre, curso_materia")
            archivo = st.file_uploader("Seleccionar archivo", type=['xlsx'])
            if archivo: st.success("Archivo listo para procesar (Función en desarrollo)")

    # --- VISTA PROFESOR ---
    else:
        st.title("📚 Mi Agenda Pedagógica")
        menu = st.tabs(["📅 Clase de Hoy", "🔍 Buscador Histórico", "🎓 Mis Alumnos"])
        
        with menu[0]:
            col_a, col_b = st.columns([1, 2])
            with col_a:
                fecha = st.date_input("Fecha", datetime.date.today())
                st.markdown('<div class="card task-alert"><h4>⚠️ Tarea Pendiente</h4><p>Revisar página 42 del Workbook.</p></div>', unsafe_allow_html=True)
            with col_b:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.text_area("¿Qué se hizo hoy?")
                st.text_area("Tarea para la próxima")
                st.checkbox("Marcar tarea anterior como cumplida")
                st.button("Guardar Clase")
                st.markdown('</div>', unsafe_allow_html=True)

        with menu[1]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            busqueda = st.text_input("🔍 Buscar por tema (ej: 'Present Perfect')")
            if busqueda: st.info(f"Buscando '{busqueda}' en años anteriores...")
            st.markdown('</div>', unsafe_allow_html=True)
