import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN (Simplificado) ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center;'>🚀 ClassTrack 360</h1>", unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
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

    # --- VISTA PROFESOR ---
    if user['rol'] != 'admin':
        st.title(f"📚 Gestión de Cursos y Alumnos 2026")
        
        tab_cursos, tab_alumnos, tab_agenda = st.tabs(["🏗️ Mis Cursos", "👥 Inscribir Alumnos", "📅 Agenda"])

        # --- SECCIÓN 1: CREAR CURSOS ---
        with tab_cursos:
            st.subheader("Crear Nueva Materia / Curso")
            with st.form("nuevo_curso"):
                nombre_materia = st.text_input("Nombre de la Materia (ej: Qui3015online)")
                horario_materia = st.text_input("Días y Horarios")
                anio = st.number_input("Año Lectivo", value=2026)
                if st.form_submit_button("Crear Curso"):
                    # Usamos la tabla 'inscripciones' para definir el curso (sin alumno aún)
                    data = {
                        "profesor_id": user['id'],
                        "nombre_curso_materia": nombre_materia,
                        "horario": horario_materia,
                        "anio_lectivo": anio
                    }
                    supabase.table("inscripciones").insert(data).execute()
                    st.success(f"Curso '{nombre_materia}' creado para el ciclo {anio}")
            
            st.divider()
            st.subheader("Cursos Activos")
            mis_cursos = supabase.table("inscripciones").select("nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).execute()
            if mis_cursos.data:
                df_cursos = pd.DataFrame(mis_cursos.data).drop_duplicates()
                st.table(df_cursos)

        # --- SECCIÓN 2: INSCRIBIR ALUMNOS EN CURSOS EXISTENTES ---
        with tab_alumnos:
            st.subheader("Inscribir Alumno en un Curso")
            # Traer solo los cursos que el profe creó
            cursos_lista = [c['nombre_curso_materia'] for c in mis_cursos.data] if mis_cursos.data else []
            
            if not cursos_lista:
                st.warning("Primero debés crear un curso en la pestaña anterior.")
            else:
                with st.form("form_alumno"):
                    curso_sel = st.selectbox("Seleccionar Curso", list(set(cursos_lista)))
                    nom_alu = st.text_input("Nombre del Alumno")
                    ape_alu = st.text_input("Apellido")
                    
                    if st.form_submit_button("Inscribir"):
                        # 1. Crear el alumno
                        alu_res = supabase.table("alumnos").insert({"nombre": nom_alu, "apellido": ape_alu}).execute()
                        if alu_res.data:
                            # 2. Buscar datos del curso para clonar la fila con el alumno
                            c_info = next(item for item in mis_cursos.data if item["nombre_curso_materia"] == curso_sel)
                            ins_data = {
                                "alumno_id": alu_res.data[0]['id'],
                                "profesor_id": user['id'],
                                "nombre_curso_materia": curso_sel,
                                "horario": c_info['horario'],
                                "anio_lectivo": c_info['anio_lectivo']
                            }
                            supabase.table("inscripciones").insert(ins_data).execute()
                            st.success(f"✅ {nom_alu} {ape_alu} agregado a {curso_sel}")

        # --- SECCIÓN 3: AGENDA (Bitácora) ---
        with tab_agenda:
            st.info("Aquí seleccionarás el curso y verás la lista de alumnos para pasar los temas del día.")
