import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; }
    .confirm-box { padding: 10px; border: 1px solid #ff4b4b; border-radius: 10px; background-color: rgba(255, 75, 75, 0.1); margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: st.error("Acceso denegado.")
else:
    user = st.session_state.user
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos", "🔍 Historial y Edición"])

    # Consultas base
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()

    # --- TAB 2: CURSOS (CON DOBLE CONFIRMACIÓN) ---
    with tabs[2]:
        st.subheader("Tus Materias")
        if res_c.data:
            for cur in res_c.data:
                col_b1, col_b2 = st.columns([4,1])
                col_b1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                
                # Lógica de confirmación local para borrar curso
                if col_b2.button("Borrar", key=f"btn_del_c_{cur['id']}"):
                    st.session_state[f"confirm_c_{cur['id']}"] = True
                
                if st.session_state.get(f"confirm_c_{cur['id']}", False):
                    st.markdown(f'<div class="confirm-box">⚠️ ¿Borrar curso y todos sus datos?</div>', unsafe_allow_html=True)
                    col_del1, col_
