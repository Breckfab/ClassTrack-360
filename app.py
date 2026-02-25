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
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; margin-bottom: 20px; }
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (VALIDADO PARA ENTER) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_final"):
            u_input = st.text_input("Usuario").strip().lower()
            p_input = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                email_real = ""
                if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
                if email_real:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p_input).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Credenciales incorrectas.")
                    except: st.error("Error de red. Reintenta.")
                else: st.error("Usuario no reconocido.")
else:
    user = st.session_state.user
    hoy = datetime.datetime.now()
    es_daguerre = "daguerre" in user['email'].lower()
    
    st.sidebar.write(f"Sesión: {'Daguerre' if es_daguerre else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA DE MATERIAS ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Búsqueda e Inscripción")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas. Primero crea una en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            with st.expander("➕ Inscribir Nuevo Alumno", expanded=True):
                with st.form("form_alu_full", clear_on_submit=True):
                    c_sel = st.selectbox("Curso destino:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
                    n_n = st.text_input("Nombre")
                    a_a = st.text_input("Apellido")
                    if st.form_submit_button("Registrar Alumno"):
                        if n_n and a_a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n_n, "apellido": a_a}).execute()
                            c_nom, c_hor = c_sel.split(" | ")
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_nom, "horario": c_hor, "anio_lectivo": 2026}).execute()
                            st.success("Alumno anotado."); st.rerun()

    # --- TABS: ASISTENCIA Y NOTAS (CORREGIDAS) ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty:
                st.markdown(f'<div class="warning-card">⚠️ Primero crea una materia en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
            else:
                materia_sel = st.selectbox(f"Elegir materia para {label}:", df_cursos['nombre_curso_materia'].unique(), key=f"sel_{i}")
                
                # Chequeo de alumnos en el curso seleccionado
                res_a = supabase.table("inscripciones").select("alumno_id").eq("nombre_curso_materia", materia_sel).not_.is_("alumno_id", "null").execute()
                
                if not res_a.data:
                    st.markdown(f'<div class="warning-card">⚠️ <b>No hay alumnos registrados aún en {materia_sel}.</b><br>Debes inscribirlos en la pestaña <b>Alumnos</b> para poder ver {label}.</div>', unsafe_allow_html=True)
                else:
                    st.success(f"Datos de {materia_sel} listos para procesar.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        
        with st.form("nuevo_curso_f"):
            nc = st.text_input("Nombre de Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Crear Materia"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias para registrar temas.</div>', unsafe_allow_html=True)
        else:
            st.info("Agenda operativa para el registro de contenidos.")
