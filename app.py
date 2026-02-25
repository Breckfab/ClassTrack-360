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
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (SEGURO PARA ENTER) ---
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
                    except: st.error("Error de conexión. Reintenta.")
                else: st.error("Usuario no reconocido.")
else:
    user = st.session_state.user
    hoy = datetime.datetime.now()
    sede_nombre = 'Daguerre' if 'daguerre' in user['email'].lower() else 'Cambridge'
    
    st.sidebar.write(f"Sesión: {sede_nombre}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA MAESTRA ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except Exception: pass

    # --- TAB 0: AGENDA (PREVISIÓN DE ERRORES DE TABLA) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Continuidad")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas. Ve a la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia de hoy:", df_cursos['nombre_curso_materia'].unique())
            
            # Bloque seguro para Bitácora
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data:
                    tarea_prev = res_b.data[0].get("tarea_proxima", "No se asignó tarea.")
                    temas_prev = res_b.data[0].get("temas_dictados", "No hay registros.")
                    st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{tarea_prev}</div>', unsafe_allow_html=True)
                    st.info(f"📍 **Continuidad:** En la clase anterior viste: {temas_prev}")
                else:
                    st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar.</b> Es el primer registro para esta materia.</div>', unsafe_allow_html=True)
            except Exception:
                st.markdown('<div class="warning-card">⚙️ <b>Configuración:</b> La bitácora se activará al guardar la primera clase.</div>', unsafe_allow_html=True)

            with st.form("form_agenda_final"):
                t_hoy = st.text_area("¿Qué temas diste hoy?")
                t_sig = st.text_area("Tarea para la próxima clase:")
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        try:
                            supabase.table("bitacora").insert({
                                "profesor_id": user['id'], "materia": c_agenda, "fecha": str(hoy.date()),
                                "temas_dictados": t_hoy, "tarea_proxima": t_sig
                            }).execute()
                            st.success("Guardado."); st.rerun()
                        except: st.error("Error al guardar. Verifica la tabla en la base de datos.")

    # --- TAB 1: ALUMNOS (CONTADORES PREVISORES) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Primero crea una materia en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            try:
                res_total = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
                total_mat = res_total.count if res_total.count else 0
                st.markdown(f'<div class="metric-card">Total Matrícula {sede_nombre} (2026): <span class="metric-value">{total_mat}</span></div>', unsafe_allow_html=True)
            except: pass

            with st.expander("➕ Inscribir Estudiante", expanded=True):
                with st.form("ins_alu_final"):
                    c_sel = st.selectbox("Asignar a:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                            st.success("Alumno anotado."); st.rerun()

    # --- TAB 2 Y 3: ASISTENCIA Y NOTAS (ERRORES PREVISTOS) ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty:
                st.markdown(f'<div class="warning-card">⚠️ Crea un curso primero.</div>', unsafe_allow_html=True)
            else:
                mat_sel = st.selectbox(f"Materia para {label}:", df_cursos['nombre_curso_materia'].unique(), key=f"s_{i}")
                res_check = supabase.table("inscripciones").select("alumno_id").eq("nombre_curso_materia", mat_sel).not_.is_("alumno_id", "null").execute()
                if not res_check.data:
                    st.markdown(f'<div class="warning-card">👤 <b>No hay alumnos registrados en {mat_sel}.</b><br>Inscribilos en la pestaña <b>Alumnos</b> primero.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warning-card">📝 <b>No hay {label} disponibles para mostrar todavía.</b></div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("nuevo_c"):
            nc, hc = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear Materia"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
