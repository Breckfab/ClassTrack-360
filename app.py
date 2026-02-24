import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN (Simplificado para el ejemplo) ---
if st.session_state.user is None:
    st.title("🚀 ClassTrack 360")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
        if res.data: 
            st.session_state.user = res.data[0]
            st.rerun()
else:
    user = st.session_state.user
    st.sidebar.write(f"👤 {user['email']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    # --- PANEL ADMIN: AGREGAR CURSOS Y ALUMNOS ---
    if user['rol'] == 'admin':
        st.title("🛡️ Gestión de Instituciones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ Inscribir Alumno Nuevo")
            with st.form("form_alumno"):
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                profe = st.selectbox("Asignar a Profesor", ["cambridge.fabianbelledi@gmail.com", "daguerre.fabianbelledi@gmail.com"])
                curso = st.text_input("Nombre del Curso/Materia", placeholder="Ej: Qui3015online")
                horario = st.text_input("Horario", placeholder="Ej: Lun y Mie 18hs")
                if st.form_submit_button("Registrar Alumno"):
                    # 1. Crear el alumno
                    alu_res = supabase.table("alumnos").insert({"nombre": nombre, "apellido": apellido}).execute()
                    if alu_res.data:
                        # 2. Crear la inscripción
                        ins_data = {
                            "alumno_id": alu_res.data[0]['id'],
                            "profesor_id": supabase.table("usuarios").select("id").eq("email", profe).execute().data[0]['id'],
                            "nombre_curso_materia": curso,
                            "horario": horario,
                            "anio_lectivo": 2026
                        }
                        supabase.table("inscripciones").insert(ins_data).execute()
                        st.success(f"✅ {nombre} inscrito en {curso}")

        with col2:
            st.subheader("📋 Lista Actual de Alumnos")
            # Traemos la lista de la base de datos
            data = supabase.table("inscripciones").select("*, alumnos(nombre, apellido)").execute()
            if data.data:
                df = pd.DataFrame([{"Alumno": f"{i['alumnos']['apellido']}, {i['alumnos']['nombre']}", "Curso": i['nombre_curso_materia'], "Profe": i['profesor_id']} for i in data.data])
                st.dataframe(df)
