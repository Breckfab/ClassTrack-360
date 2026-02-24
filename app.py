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

# --- ESTILO (Mantenemos tu diseño sofisticado) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    # (Misma lógica de login con Enter que ya validamos)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
else:
    user = st.session_state.user
    st.sidebar.write(f"Profe: {user['email']}")
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos", "🔍 Historial/Borrados"])

    # --- TABS DE GESTIÓN CON BORRADO ---
    
    with tabs[2]: # CURSOS
        st.subheader("Tus Materias Activas")
        mis_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        if mis_c.data:
            for c in mis_c.data:
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{c['nombre_curso_materia']}** - {c['horario']}")
                if col_c2.button("Borrar Curso", key=f"del_c_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            n_m = st.text_input("Nueva Materia")
            h_m = st.text_input("Nuevo Horario")
            if st.form_submit_button("Añadir Curso"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n_m, "horario": h_m, "anio_lectivo": 2026}).execute()
                st.rerun()

    with tabs[1]: # ALUMNOS
        st.subheader("Lista de Alumnos")
        # Traer inscripciones que tengan alumno vinculado
        mis_a = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", user['id']).not_.is_("alumno_id", "null").execute()
        if mis_a.data:
            for a in mis_a.data:
                col_a1, col_a2 = st.columns([4, 1])
                col_a1.write(f"👤 {a['alumnos']['apellido']}, {a['alumnos']['nombre']} ({a['nombre_curso_materia']})")
                if col_a2.button("Dar de Baja", key=f"del_a_{a['id']}"):
                    supabase.table("inscripciones").delete().eq("id", a['id']).execute()
                    st.rerun()

    with tabs[3]: # HISTORIAL Y BORRADO DE CLASES
        st.subheader("Historial de Bitácora")
        clases = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).order("fecha", desc=True).execute()
        if clases.data:
            for cl in clases.data:
                with st.expander(f"📅 {cl['fecha']} - {cl['docente_nombre']}"):
                    st.write(f"**Temas:** {cl['temas']}")
                    st.write(f"**Tarea:** {cl['tarea_descripcion']} (Vence: {cl['tarea_vencimiento']})")
                    if st.button("Eliminar esta Clase", key=f"del_cl_{cl['id']}"):
                        supabase.table("bitacora").delete().eq("id", cl['id']).execute()
                        st.rerun()
