import streamlit as st
import streamlit.components.v1 as components
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
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE LOGIN (CALLBACK PARA ENTER) ---
def realizar_login():
    u = st.session_state.u_final.strip().lower()
    p = st.session_state.p_final
    
    email_real = ""
    if u == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
    elif u == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
    
    if email_real:
        try:
            res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
            if res.data:
                st.session_state.user = res.data[0]
            else:
                st.error("usuario o contraseña incorrecta. Intente nuevamente.")
        except:
            st.error("Error de conexión. Intente nuevamente.")
    else:
        st.error("usuario o contraseña incorrecta. Intente nuevamente.")

# --- UI PRINCIPAL ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        st.text_input("Usuario", key="u_final")
        st.text_input("Clave", type="password", key="p_final")
        st.button("Entrar", on_click=realizar_login, use_container_width=True)
else:
    # --- RELOJ DINÁMICO (BLANCO, SIN NEGRITA) ---
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora_dt = datetime.datetime.now()
    fecha_hoy = f"{ahora_dt.day} de {meses[ahora_dt.month - 1]} de {ahora_dt.year}"
    
    components.html(f"""
        <div style="text-align: right; color: white; font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; padding-right: 10px;">
            {fecha_hoy} | <span id="clock"></span>
        </div>
        <script>
            function updateClock() {{
                const d = new Date();
                document.getElementById('clock').innerHTML = d.toLocaleTimeString('es-AR', {{hour12:false}});
            }}
            setInterval(updateClock, 1000);
            updateClock();
        </script>
    """, height=35)

    user = st.session_state.user
    sede_nombre = 'Daguerre' if 'daguerre' in user['email'].lower() else 'Cambridge'
    
    with st.sidebar:
        st.write(f"📍 Sede: {sede_nombre}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de materias
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (ORDEN PEDAGÓGICO) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas. Ve a la pestaña Cursos.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            
            # Recuperar Tarea de la clase anterior
            tarea_para_hoy = ""
            temas_anteriores = ""
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data:
                    tarea_para_hoy = res_b.data[0].get("tarea_proxima", "")
                    temas_anteriores = res_b.data[0].get("temas_dictados", "")
            except: pass

            if tarea_para_hoy:
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy (de la clase anterior):</b><br>{tarea_para_hoy}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar hoy.</b>
