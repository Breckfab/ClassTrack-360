import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; text-align: center; margin-bottom: 20px; }
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 20px; border-radius: 10px; margin: 10px 0; color: #ffb800; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CORREGIDO PARA ENTER Y CAMBIO A 'USUARIO') ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        # El uso de st.form es lo que permite que el ENTER funcione sin errores de red
        with st.form("login_final"):
            u_input = st.text_input("Usuario").strip().lower()
            p_input = st.text_input("Clave", type="password")
            submit_button = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_button:
                email_real = ""
                if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
                
                if email_real:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p_input).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas.")
                    except:
                        st.error("Error de conexión con el servidor. Intenta nuevamente.")
                else:
                    st.error("Usuario no reconocido.")

else:
    user = st.session_state.user
    hoy = datetime.datetime.now()
    es_daguerre = "daguerre" in user['email'].lower()
    
    st.sidebar.write(f"Sesión activa: {'Daguerre' if es_daguerre else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga base de datos de cursos para el profesor
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            df_cursos = pd.DataFrame(res_c.data)
    except:
        pass

    # --- PESTAÑAS CON PROTECCIÓN DE PANTALLA NEGRA ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>Paso 1:</b> Primero debes crear una materia en la pestaña <b>Cursos</b> para poder inscribir alumnos.</div>', unsafe_allow_html=True)
        else:
            st.info("Buscador e inscripción de alumnos habilitados.")
            # Aquí va el código de inscripción que ya teníamos

    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                st.write(f"📘 {cur['nombre_curso_materia']} - {cur['horario']}")
        
        with st.form("nuevo_c"):
            st.write("➕ Añadir Materia")
            n = st.text_input("Nombre de Materia")
            h = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if n and h:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n, "horario": h, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # Mensaje guía para el resto de pestañas
    for i, label in [(0, "Agenda"), (2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty:
                st.markdown(f'<div class="warning-card">⚠️ No se encontró información de cursos. Por favor, crea uno en la pestaña <b>Cursos</b> para activar la {label}.</div>', unsafe_allow_html=True)
            else:
                st.info(f"Selecciona un curso en la parte superior para ver los datos de {label}.")
