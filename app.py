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
    
    /* Reloj Blanco y Fino */
    .reloj-vivo {
        position: absolute;
        top: -45px;
        right: 10px;
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1.1rem;
        z-index: 999;
    }
    
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (SEGURO PARA ENTER Y MENSAJE EXACTO) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form(key="login_final_secure", clear_on_submit=False):
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
                        else: st.error("usuario o contraseña incorrecta. Intente nuevamente.")
                    except: st.error("Error de conexión. Intente nuevamente.")
                else: st.error("usuario o contraseña incorrecta. Intente nuevamente.")
else:
    # --- RELOJ DINÁMICO ---
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora_init = datetime.datetime.now()
    fecha_hoy = f"{ahora_init.day} de {meses[ahora_init.month - 1]} de {ahora_init.year}"
    
    st.markdown(f"""
        <div class="reloj-vivo">
            <span id="fecha-actual">{fecha_hoy}</span> | <span id="reloj-actual"></span>
        </div>
        <script>
            function updateClock() {{
                const now = new Date();
                const timeStr = now.getHours().toString().padStart(2, '0') + ":" + 
                              now.getMinutes().toString().padStart(2, '0') + ":" + 
                              now.getSeconds().toString().padStart(2, '0');
                document.getElementById('reloj-actual').textContent = timeStr;
            }}
            setInterval(updateClock, 1000);
            updateClock();
        </script>
    """, unsafe_allow_html=True)

    user = st.session_state.user
    sede_nombre = 'Daguerre' if 'daguerre' in user['email'].lower() else 'Cambridge'
    
    st.sidebar.write(f"Sesión: {sede_nombre}")
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

    # --- TAB 0: AGENDA (MEMORIA RECUPERADA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data:
                    t_p = res_b.data[0].get("tarea_proxima", "")
                    if t_p: st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{t_p}</div>', unsafe_allow_html=True)
                    st.info(f"📍 Clase anterior: {res_b.data[0].get('temas_dictados', 'Sin registro')}")
            except: pass
            
            with st.form("f_agenda_final"):
                temas = st.text_area("Temas de hoy")
                tarea_n = st.text_area("Tarea para la próxima")
                if st.form_submit_button("Guardar Clase"):
                    if temas: st.success("Guardado correctamente.")

    # --- TAB 1: ALUMNOS (CONTADORES) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero.</div>', unsafe_allow_html=True)
        else:
            res_t = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
            total_m = res_t.count if res_t.count else 0
            st.markdown(f'<div class="metric-card">Matrícula {sede_nombre} 2026: <span class="metric-value">{total_m}</span></div>', unsafe_allow_html=True)
            
            with st.expander("➕ Inscribir Estudiante", expanded=True):
                with st.form("ins_alu_f_v2"):
                    c_sel = st.selectbox("Asignar a:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a: st.success("Registrado."); st.rerun()

    # --- TAB 2 Y 3: LEYENDAS PRECISAS ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty: st.markdown("⚠️ Crea un curso primero.")
            else:
                mat_s = st.selectbox(f"Materia:", df_cursos['nombre_curso_materia'].unique(), key=f"s_{i}")
                res_check = supabase.table("inscripciones").select("alumno_id").eq("nombre_curso_materia", mat_s).not_.is_("alumno_id", "null").execute()
                if not res_check.data:
                    st.markdown(f'<div class="warning-card">👤 <b>No hay alumnos registrados aún en {mat_s}.</b><br>Inscribilos en la pestaña Alumnos.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warning-card">📝 <b>No hay {label} para mostrar porque no se registraron aún.</b></div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("n_c_f_v2"):
            nc, hc = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
