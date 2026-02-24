import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center;'>🚀 ClassTrack 360</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
        if res.data: 
            st.session_state.user = res.data[0]
            st.rerun()
else:
    user = st.session_state.user
    st.sidebar.write(f"👤 **{user['email']}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    st.title(f"📚 Gestión Académica")
    
    tabs = st.tabs(["🏗️ Definir Cursos", "👥 Cargar Alumnos", "📅 Agenda Diaria"])

    # 1. DEFINIR CURSOS (Ahora valida por Nombre + Horario)
    with tabs[0]:
        st.subheader("Configuración de Materias/Cursos")
        with st.form("crear_curso"):
            nom_c = st.text_input("Nombre del Curso (ej: FCE Ready)").strip()
            hor_c = st.text_input("Horario (ej: Lun-Mie 18:00)").strip()
            anio_c = st.number_input("Año Lectivo", value=2026)
            
            if st.form_submit_button("Dar de Alta Curso"):
                # VALIDACIÓN MEJORADA: Verificamos nombre Y horario para el mismo profe y año
                check = supabase.table("inscripciones").select("*").eq("profesor_id", user['id']).eq("nombre_curso_materia", nom_c).eq("horario", hor_c).eq("anio_lectivo", anio_c).execute()
                
                if check.data:
                    st.warning(f"⚠️ Ya existe el curso '{nom_c}' en el horario '{hor_c}' para el {anio_c}.")
                else:
                    supabase.table("inscripciones").insert({
                        "profesor_id": user['id'],
                        "nombre_curso_materia": nom_c,
                        "horario": hor_c,
                        "anio_lectivo": anio_c
                    }).execute()
                    st.success(f"✅ Curso '{nom_c}' ({hor_c}) creado con éxito.")

    # 2. CARGAR ALUMNOS (Selector combinado)
    with tabs[1]:
        st.subheader("Inscripción de Estudiantes")
        # Traemos todos los cursos
        mis_cursos_raw = supabase.table("inscripciones").select("nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).execute()
        
        if not mis_cursos_raw.data:
            st.info("Aún no tienes cursos creados.")
        else:
            # Creamos una lista de opciones que muestre Nombre + Horario para diferenciar
            df_mostrar = pd.DataFrame(mis_cursos_raw.data).drop_duplicates()
            opciones_cursos = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_mostrar.iterrows()]
            
            with st.form("inscripcion_alu"):
                seleccion = st.selectbox("Elegir Curso y Horario", opciones_cursos)
                n_alu = st.text_input("Nombre")
                a_alu = st.text_input("Apellido")
                
                if st.form_submit_button("Registrar Alumno"):
                    # Separamos la selección para buscar en la base de datos
                    c_nombre, c_horario = seleccion.split(" | ")
                    c_data = next(item for item in mis_cursos_raw.data if item["nombre_curso_materia"] == c_nombre and item["horario"] == c_horario)
                    
                    nuevo_alu = supabase.table("alumnos").insert({"nombre": n_alu, "apellido": a_alu}).execute()
                    
                    if nuevo_alu.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": nuevo_alu.data[0]['id'],
                            "profesor_id": user['id'],
                            "nombre_curso_materia": c_nombre,
                            "horario": c_horario,
                            "anio_lectivo": c_data['anio_lectivo']
                        }).execute()
                        st.success(f"✅ {n_alu} {a_alu} inscrito en {c_nombre} ({c_horario}).")
