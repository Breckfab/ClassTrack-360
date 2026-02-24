import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px; }
    .stButton>button { background-image: linear-gradient(to right, #4f46e5, #7c3aed); color: white; border-radius: 10px; border: none; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DE LOGIN (Simplificada) ---
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
        st.info("Desde aquí supervisas todo. Para cargar alumnos específicos, entra con los mails de Cambridge o Daguerre.")

    # --- VISTA PROFESOR (CAMBRIDGE / DAGUERRE) ---
    else:
        inst = "Cambridge" if "cambridge" in user['email'] else "Daguerre"
        st.title(f"📚 Gestión {inst}")
        
        tabs = st.tabs(["📅 Agenda Diaria", "👥 Gestión de Alumnos", "🔍 Buscador"])

        with tabs[1]:  # Pestaña de Alumnos
            st.subheader(f"➕ Nueva Inscripción en {inst}")
            with st.form("nuevo_alumno"):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre")
                apellido = c1.text_input("Apellido")
                curso = c2.text_input("Curso o Materia (ej: Qui3015online)")
                horario = c2.text_input("Día y Horario")
                
                if st.form_submit_button("Inscribir Alumno"):
                    # 1. Crear Alumno
                    a_res = supabase.table("alumnos").insert({"nombre": nombre, "apellido": apellido}).execute()
                    if a_res.data:
                        # 2. Vincular con el profesor actual
                        ins = {
                            "alumno_id": a_res.data[0]['id'],
                            "profesor_id": user['id'],
                            "nombre_curso_materia": curso,
                            "horario": horario,
                            "anio_lectivo": 2026
                        }
                        supabase.table("inscripciones").insert(ins).execute()
                        st.success(f"Alumno {apellido} cargado correctamente.")
            
            st.divider()
            st.subheader("📋 Mis Alumnos y Cursos Actuales")
            # Filtrar solo alumnos del profesor logueado
            mis_alumnos = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, alumnos(nombre, apellido)").eq("profesor_id", user['id']).execute()
            
            if mis_alumnos.data:
                for a in mis_alumnos.data:
                    with st.expander(f"👤 {a['alumnos']['apellido']}, {a['alumnos']['nombre']} - {a['nombre_curso_materia']}"):
                        st.write(f"**Horario:** {a['horario']}")
                        if st.button("Dar de Baja", key=a['id']):
                            supabase.table("inscripciones").delete().eq("id", a['id']).execute()
                            st.rerun()
            else:
                st.info("Aún no tienes alumnos cargados.")

        with tabs[0]: # Agenda Diaria (Lo mismo que antes pero filtrando por tus cursos)
            st.write("Aquí aparecerán tus cursos para registrar la bitácora.")
