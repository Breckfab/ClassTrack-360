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

# --- ESTILO CSS (DISEÑO DEGRADADO DEEP OCEAN + CRISTAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp { 
        background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); 
        color: #e0e0e0; 
        font-family: 'Inter', sans-serif; 
    }
    
    .login-box {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        text-align: center;
    }

    .logo-text { 
        font-weight: 800; 
        background: linear-gradient(to right, #3b82f6, #a855f7); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-bottom: 10px; 
    }
    
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; margin-bottom: 10px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFAZ ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div><p style="color:#94a3b8">Ingreso al Panel Docente</p></div>', unsafe_allow_html=True)
        
        with st.form("login_form_final_v2"):
            u_input = st.text_input("Usuario", placeholder="Nombre de sede").strip().lower()
            p_input = st.text_input("Clave", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Acceder al Sistema", use_container_width=True)
            
            if submit:
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
                            st.error("usuario o contraseña incorrecta. Intente nuevamente.")
                    except:
                        st.error("Error de conexión con la base de datos.")
                else:
                    st.error("usuario o sede no reconocida.")
else:
    # --- RELOJ DINÁMICO ---
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
                const hh = String(d.getHours()).padStart(2, '0');
                const mm = String(d.getMinutes()).padStart(2, '0');
                const ss = String(d.getSeconds()).padStart(2, '0');
                document.getElementById('clock').innerHTML = hh + ":" + mm + ":" + ss;
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

    # Carga global de cursos
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c and res_c.data:
            df_cursos = pd.DataFrame(res_c.data)
    except:
        pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            tarea_anterior = ""
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b and res_b.data:
                    tarea_anterior = res_b.data[0].get("tarea_proxima", "")
            except:
                pass

            if tarea_anterior:
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy:</b><br>{tarea_anterior}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar hoy.</b></div>', unsafe_allow_html=True)

            with st.form("form_agenda_completo_v16"):
                t_hoy = st.text_area("Temas dictados hoy")
                t_proxima = st.text_area("Tarea para la próxima")
                f_proxima = st.date_input("Fecha entrega:", value=ahora_dt + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        try:
                            t_txt = f"[{f_proxima.strftime('%d/%m/%Y')}] {t_proxima}"
                            supabase.table("bitacora").insert({"profesor_id": user['id'], "materia": c_agenda, "fecha": str(ahora_dt.date()), "temas_dictados": t_hoy, "tarea_proxima": t_txt}).execute()
                            st.success("Guardado."); st.rerun()
                        except:
                            st.error("Error al guardar.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero.</div>', unsafe_allow_html=True)
        else:
            try:
                res_t = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
                st.markdown(f'<div class="metric-card">Matrícula {sede_nombre} 2026: <span class="metric-value">{res_t.count if res_t and res_t.count else 0}</span></div>', unsafe_allow_html=True)
                
                mat_f = st.selectbox("Ver alumnos de:", df_cursos['nombre_curso_materia'].unique(), key="sel_alu_v16")
                res_alu = supabase.table("inscripciones").select("alumnos(nombre, apellido)").eq("profesor_id", user['id']).eq("nombre_curso_materia", mat_f).not_.is_("alumno_id", "null").execute()
                if res_alu and res_alu.data:
                    for a in res_alu.data:
                        if a and 'alumnos' in a and a['alumnos']:
                            st.write(f"• {a['alumnos'].get('apellido', '')}, {a['alumnos'].get('nombre', '')}")
            except:
                st.error("Error al cargar lista.")

            with st.expander("➕ Inscribir Estudiante"):
                with st.form("ins_alu_f_v16"):
                    c_sel = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                            st.success("Inscrito."); st.rerun()

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if df_cursos.empty:
            st.markdown("⚠️ Crea un curso primero.")
        else:
            mat_asis = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique(), key="asis_mat_v16")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", mat_asis).not_.is_("alumno_id", "null").execute()
            if res_a and res_a.data:
                with st.form("form_asis_v16"):
                    asis_data = []
                    for item in res_a.data:
                        if item and 'alumnos' in item and item['alumnos']:
                            alu = item['alumnos']
                            col1, col2 = st.columns([3, 1])
                            col1.write(f"{alu.get('apellido')}, {alu.get('nombre')}")
                            estado = col2.radio("Estado:", ["P", "A"], key=f"r_{alu['id']}", horizontal=True)
                            asis_data.append({"id": alu['id'], "estado": estado})
                    if st.form_submit_button("Guardar Asistencia"):
                        st.success("Asistencia procesada.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Calificaciones")
        if df_cursos.empty:
            st.markdown("⚠️ Crea un curso primero.")
        else:
            mat_n = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique(), key="notas_mat_v16")
            res_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", mat_n).not_.is_("alumno_id", "null").execute()
            if res_n and res_n.data:
                with st.form("form_notas_v16"):
                    for item in res_n.data:
                        if item and 'alumnos' in item and item['alumnos']:
                            alu = item['alumnos']
                            st.number_input(f"{alu.get('apellido')}", 1, 10, step=1, key=f"n_{alu['id']}")
                    if st.form_submit
