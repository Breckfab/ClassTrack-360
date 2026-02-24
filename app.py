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
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    st.title("📑 Mi Gestión Académica")
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

    # --- PESTAÑA CURSOS (CORREGIDA) ---
    with tabs[2]:
        st.subheader("Configuración de Materias 2026")
        with st.form("form_crear_curso", clear_on_submit=True):
            n_materia = st.text_input("Nombre de la Materia")
            h_materia = st.text_input("Horario")
            btn_crear = st.form_submit_button("Guardar Materia")
            
            if btn_crear:
                if n_materia and h_materia:
                    # Inserción directa
                    data = {
                        "profesor_id": user['id'], 
                        "nombre_curso_materia": n_materia, 
                        "horario": h_materia, 
                        "anio_lectivo": 2026
                    }
                    try:
                        supabase.table("inscripciones").insert(data).execute()
                        st.success(f"✅ ¡Curso '{n_materia}' creado con éxito!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
                else:
                    st.warning("⚠️ Completá todos los campos.")

    # --- PESTAÑA ALUMNOS ---
    with tabs[1]:
        st.subheader("Inscripción de Alumnos")
        # Traer cursos para el selector
        mis_cursos = supabase.table("inscripciones").select("nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        
        if mis_cursos.data:
            df_c = pd.DataFrame(mis_cursos.data).drop_duplicates()
            lista_select = [f"{r['nombre_curso_materia']} | {r['horario']}" for _, r in df_c.iterrows()]
            
            with st.form("form_inscripcion", clear_on_submit=True):
                curso_elegido = st.selectbox("Elegir Curso", lista_select)
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                if st.form_submit_button("Inscribir Alumno"):
                    # 1. Crear alumno
                    res_a = supabase.table("alumnos").insert({"nombre": nom_a, "apellido": ape_a}).execute()
                    if res_a.data:
                        # 2. Vincular
                        c_nom, c_hor = curso_elegido.split(" | ")
                        supabase.table("inscripciones").insert({
                            "alumno_id": res_a.data[0]['id'],
                            "profesor_id": user['id'],
                            "nombre_curso_materia": c_nom,
                            "horario": c_hor,
                            "anio_lectivo": 2026
                        }).execute()
                        st.success(f"✅ {nom_a} {ape_a} agregado.")
        else:
            st.info("Primero creá un curso en la pestaña de al lado.")

    # --- PESTAÑA AGENDA (BITÁCORA) ---
    with tabs[0]:
        st.subheader("Bitácora Diaria")
        # Aquí irá la lógica de carga de temas y tareas que vimos antes
        st.info("Elegí un curso y registrá lo que diste hoy.")
