import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        padding: 25px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .logo-text {
        font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #3b82f6, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 3rem; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div style="text-align: center;"><svg viewBox="0 0 120 80" width="150"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#3b82f6;"/><stop offset="100%" style="stop-color:#a855f7;"/></linearGradient></defs><path d="M10 40 Q 60 0 110 40 Q 60 80 10 40" fill="none" stroke="url(#g)" stroke-width="3" /><circle cx="60" cy="40" r="18" fill="rgba(59, 130, 246, 0.1)" stroke="url(#g)" stroke-width="2" /><text x="60" y="44" font-family="Arial" font-weight="800" font-size="10" fill="white" text-anchor="middle">360</text></svg></div>""", unsafe_allow_html=True)
        st.markdown("<div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: st.error("Acceso denegado.")

# --- PANEL INTERNO ---
else:
    user = st.session_state.user
    st.sidebar.markdown("<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    st.title("📑 Mi Gestión Académica")
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

    # TAB 2: CURSOS
    with tabs[2]:
        st.subheader("Cursos 2026")
        with st.form("c_curso"):
            n_c = st.text_input("Materia")
            h_c = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n_c, "horario": h_c, "anio_lectivo": 2026}).execute()
                st.success("Curso creado.")
                st.rerun()

    # TAB 1: ALUMNOS
    with tabs[1]:
        st.subheader("Alumnos")
        res_c = supabase.table("inscripciones").select("nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        if res_c.data:
            df_c = pd.
