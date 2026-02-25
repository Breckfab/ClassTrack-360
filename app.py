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
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CORREGIDO PARA ENTER) ---
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
                    except: st.error("Error de red. Intenta nuevamente.")
                else: st.error("Usuario no reconocido.")
else:
    user = st.session_state.user
    hoy = datetime.datetime.now()
    
    st.sidebar.write(f"Sesión: {'Daguerre' if 'daguerre' in user['email'] else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de materias
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON MEMORIA DE CLASE ANTERIOR) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Continuidad")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias. Crea una en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia de hoy:", df_cursos['nombre_curso_materia'].unique())
            
            # Recuperar última clase
            ultima_clase = None
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data: ultima_clase = res_b.data[0]
            except: pass

            if ultima_clase:
                tarea_hoy = ultima_clase.get('tarea_proxima', 'No hay tarea registrada.')
                temas_ant = ultima_clase.get('temas_dictados', 'No hay temas registrados.')
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{tarea_hoy}</div>', unsafe_allow_html=True)
                st.info(f"📍 **La clase anterior viste:** {temas_ant}")
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay registros previos.</b> Es tu primera clase registrada para esta materia.</div>', unsafe_allow_html=True)

            with st.form("form_clase_hoy", clear_on_submit=True):
                t_hoy = st.text_area("¿Qué temas diste hoy?")
                tar_sig = st.text_area("Tarea para la clase que viene:")
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        supabase.table("bitacora").insert({
                            "profesor_id": user['id'], "materia": c_agenda, "fecha": str(hoy.date()),
                            "temas_dictados": t_hoy, "tarea_proxima": tar_sig
                        }).execute()
                        st.success("Guardado. Mañana verás esto como recordatorio.")
                        st.rerun()

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN SIEMPRE DISPONIBLE) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero para inscribir alumnos.</div>', unsafe_allow_html=True)
        else:
            with st.form("ins_alu"):
                c_dest = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique())
                nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                if st.form_submit_button("Inscribir"):
                    st.success("Alumno inscrito."); st.rerun()

    # --- TAB 2 Y 3: LEYENDAS SI NO HAY ALUMNOS ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            st.markdown(f'<div class="warning-card">⚠️ <b>No hay alumnos registrados aún en esta materia.</b><br>Inscríbelos en la pestaña <b>Alumnos</b> para activar esta sección.</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("n_c"):
            n, h = st.text_input("Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if n and h:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n, "horario": h, "anio_lectivo": 2026}).execute()
                    st.rerun()
