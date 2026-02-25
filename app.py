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

# --- LÓGICA DE LOGIN ---
def realizar_login():
    u = st.session_state.u_final.strip().lower()
    p = st.session_state.p_final
    email_real = ""
    if u == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
    elif u == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
    
    if email_real:
        try:
            res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]
            else: st.error("usuario o contraseña incorrecta. Intente nuevamente.")
        except: st.error("Error de conexión. Intente nuevamente.")
    else: st.error("usuario o contraseña incorrecta. Intente nuevamente.")

# --- UI PRINCIPAL ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        st.text_input("Usuario", key="u_final")
        st.text_input("Clave", type="password", key="p_final")
        st.button("Entrar", on_click=realizar_login, use_container_width=True)
else:
    # --- RELOJ DINÁMICO ---
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora_dt = datetime.datetime.now()
    fecha_hoy_str = f"{ahora_dt.day} de {meses[ahora_dt.month - 1]} de {ahora_dt.year}"
    
    components.html(f"""
        <div style="text-align: right; color: white; font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; padding-right: 10px;">
            {fecha_hoy_str} | <span id="clock"></span>
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

    # --- TAB 0: AGENDA (CON FLUJO PEDAGÓGICO) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            
            # 1. Recuperar Tarea para Hoy y Clase Anterior
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data:
                    tarea_p = res_b.data[0].get("tarea_proxima", "")
                    if tarea_p:
                        st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy:</b><br>{tarea_p}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="reminder-box">✅ <b>No hay tarea para hoy.</b></div>', unsafe_allow_html=True)
                    st.info(f"📍 Hilo conductor (Clase anterior): {res_b.data[0].get('temas_dictados', 'Sin registro')}")
                else:
                    st.markdown('<div class="reminder-box">📝 Primera clase: No hay registros previos.</div>', unsafe_allow_html=True)
            except: pass
            
            # 2. Formulario de Clase Actual
            with st.form("f_agenda_v8"):
                temas = st.text_area("Temas dictados hoy")
                st.write("---")
                tarea_n = st.text_area("Tarea para la próxima clase")
                fecha_tarea = st.date_input("Tarea para el día:", value=ahora_dt + datetime.timedelta(days=7))
                
                if st.form_submit_button("Guardar Registro"):
                    if temas:
                        try:
                            supabase.table("bitacora").insert({
                                "profesor_id": user['id'], 
                                "materia": c_agenda, 
                                "fecha": str(ahora_dt.date()), 
                                "temas_dictados": temas, 
                                "tarea_proxima": f"[{fecha_tarea.strftime('%d/%m/%Y')}] {tarea_n}"
                            }).execute()
                            st.success("Clase guardada."); st.rerun()
                        except: st.error("Error al guardar.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero.</div>', unsafe_allow_html=True)
        else:
            res_t = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
            st.markdown(f'<div class="metric-card">Matrícula {sede_nombre} 2026: <span class="metric-value">{res_t.count if res_t.count else 0}</span></div>', unsafe_allow_html=True)
            
            with st.expander("➕ Inscribir Estudiante"):
                with st.form("ins_alu_v8"):
                    c_sel = st.selectbox("Asignar a:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                            st.success("Alumno anotado."); st.rerun()

    # --- TAB 2 Y 3: LEYENDAS ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty: st.markdown("⚠️ Crea un curso primero.")
            else:
                mat_s = st.selectbox(f"Materia:", df_cursos['nombre_curso_materia'].unique(), key=f"s_{i}")
                st.markdown(f'<div class="warning-card">📝 <b>No hay {label} para mostrar porque no se registraron aún.</b></div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("n_c_v8"):
            nc, hc = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
