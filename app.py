import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO CSS (MODERNO Y SOFISTICADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button { 
        background-image: linear-gradient(to right, #2563eb, #7c3aed);
        color: white; border-radius: 8px; border: none; font-weight: 500;
        padding: 0.6rem 2rem; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 4px 12px rgba(37, 99, 235, 0.3); }
    .card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 15px;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE (breckfab@gmail.com) ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- PANTALLA DE LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Espacio para el logo del Ojo 360
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/Breckfab/ClassTrack-360/main/logo.png", width=250) # Asegúrate de subirlo a GitHub con este nombre
        st.markdown("<h1 style='text-align: center;'>ClassTrack 360</h1>", unsafe_allow_html=True)
        
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

# --- PANEL INTERNO ---
else:
    user = st.session_state.user
    st.sidebar.image("https://raw.githubusercontent.com/Breckfab/ClassTrack-360/main/logo.png", width=100)
    st.sidebar.markdown(f"**Sesión:** {user['email']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    # VISTA ADMINISTRADOR
    if user['rol'] == 'admin':
        st.title("🛡️ Consola de Control")
        st.markdown('<div class="card">Bienvenido Fabián. Control global de instituciones activado.</div>', unsafe_allow_html=True)
        # Aquí se listan los usuarios de breckfab@gmail.com
    
    # VISTA PROFESOR (CAMBRIDGE / DAGUERRE)
    else:
        st.title("📑 Gestión Académica")
        tabs = st.tabs(["🏗️ Definir Cursos", "👥 Inscripción", "📅 Agenda Diaria"])

        # PESTAÑA 1: CREAR CURSO (Valida Nombre + Horario + Año)
        with tabs[0]:
            st.subheader("Alta de Materias")
            with st.form("nuevo_curso"):
                nom = st.text_input("Materia (ej: FCE Ready)").strip()
                hor = st.text_input("Horario (ej: Martes 10:00)").strip()
                anio = st.number_input("Ciclo Lectivo", value=2026)
                if st.form_submit_button("Guardar Curso"):
                    # Verificación de duplicados
                    check = supabase.table("inscripciones").select("*").eq("profesor_id", user['id']).eq("nombre_curso_materia", nom).eq("horario", hor).eq("anio_lectivo", anio).execute()
                    if check.data:
                        st.warning("Este curso ya existe con ese horario.")
                    else:
                        supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nom, "horario": hor, "anio_lectivo": anio}).execute()
                        st.success("Curso creado.")

        # PESTAÑA 2: CARGAR ALUMNOS
        with tabs[1]:
            st.subheader("Registro de Alumnos")
            cursos_raw = supabase.table("inscripciones").select("nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).execute()
            if not cursos_raw.data:
                st.info("Crea un curso primero.")
            else:
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for c in pd.DataFrame(cursos_raw.data).drop_duplicates().to_dict('records')]
                with st.form("form_alu"):
                    sel = st.selectbox("Curso", opciones)
                    n = st.text_input("Nombre")
                    a = st.text_input("Apellido")
                    if st.form_submit_button("Registrar"):
                        c_nom, c_hor = sel.split(" | ")
                        c_dat = next(item for item in cursos_raw.data if item["nombre_curso_materia"] == c_nom and item["horario"] == c_hor)
                        alu = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                        if alu.data:
                            supabase.table("inscripciones").insert({"alumno_id": alu.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_nom, "horario": c_hor, "anio_lectivo": c_dat['anio_lectivo']}).execute()
                            st.success("Alumno inscrito.")
