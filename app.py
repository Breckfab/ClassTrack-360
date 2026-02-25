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

# --- LOGIN ---
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
                    except: st.error("Error de conexión.")
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

    # Carga de materias
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON MANEJO DE ERROR DE TABLA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            
            # Bloque seguro para evitar el error de API
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data:
                    st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{res_b.data[0].get("tarea_proxima", "No hay")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="reminder-box">✅ No hay registros previos.</div>', unsafe_allow_html=True)
            except Exception:
                st.markdown('<div class="warning-card">⚙️ <b>Configuración pendiente:</b> La tabla de Bitácora se activará automáticamente al guardar tu primera clase.</div>', unsafe_allow_html=True)

            with st.form("f_agenda"):
                temas = st.text_area("Temas dictados hoy")
                tarea = st.text_area("Tarea para la próxima clase")
                if st.form_submit_button("Guardar Clase"):
                    if temas:
                        try:
                            supabase.table("bitacora").insert({
                                "profesor_id": user['id'], "materia": c_agenda, "fecha": str(hoy.date()),
                                "temas_dictados": temas, "tarea_proxima": tarea
                            }).execute()
                            st.success("Guardado correctamente.")
                            st.rerun()
                        except: st.error("Falta crear la tabla 'bitacora' en Supabase.")

    # --- TAB 1: ALUMNOS (CONTADORES) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero.</div>', unsafe_allow_html=True)
        else:
            # Estadísticas rápidas
            res_total = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
            count_total = res_total.count if res_total.count else 0
            
            st.markdown(f'<div class="metric-card">Total Matrícula {sede_nombre} 2026: <span class="metric-value">{count_total}</span></div>', unsafe_allow_html=True)
            
            with st.expander("➕ Inscribir Estudiante", expanded=True):
                with st.form("ins_alu"):
                    c_sel = st.selectbox("Asignar a:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                            supabase.table("inscripciones").insert({
                                "alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], 
                                "nombre_curso_materia": c_sel, "anio_lectivo": 2026
                            }).execute()
                            st.success("Alumno anotado."); st.rerun()

    # --- TABS ASISTENCIA Y NOTAS ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty: st.markdown("⚠️ Crea un curso primero.")
            else:
                mat = st.selectbox(f"Materia:", df_cursos['nombre_curso_materia'].unique(), key=f"s_{i}")
                st.markdown(f'<div class="warning-card">📝 No hay {label} disponibles para mostrar todavía en {mat}.</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("n_c"):
            nc, hc = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
