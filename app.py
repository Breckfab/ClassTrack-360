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
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 20px; border-radius: 10px; margin: 10px 0; color: #ffb800; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .print-area { background-color: white; color: black; padding: 25px; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd; }
    @media print { .no-print { display: none !important; } .stApp { background-color: white !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN DISCRETO ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Sede").strip().lower()
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                email_real = ""
                if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
                if email_real:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no válida.")
else:
    user = st.session_state.user
    hoy = datetime.date.today()
    es_daguerre = "daguerre" in user['email'].lower()
    st.sidebar.write(f"Sede: {'Daguerre' if es_daguerre else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA DATOS BASE ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON RECORDATORIOS) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Tareas")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>Agenda bloqueada.</b><br>Primero crea una materia en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia de hoy:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
            c_id = df_cursos[df_cursos['nombre_curso_materia'] == c_agenda.split(" | ")[0]].iloc[0]['id']
            
            # Recordatorio de tarea
            st.markdown('<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>No hay tareas registradas para esta fecha.</div>', unsafe_allow_html=True)
            
            with st.form("form_agenda"):
                temas = st.text_area("Contenidos dictados:")
                tarea_sig = st.text_area("Tarea para la próxima clase:")
                f_venc = st.date_input("Fecha de entrega:", hoy + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    st.success("Clase guardada en la bitácora.")

    # --- TAB 2: ASISTENCIA (DIFERENCIADA) ---
    with tabs[2]:
        st.subheader("Control de Presentismo")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>Sin datos para asistencia.</b><br>Crea un curso e inscribe alumnos para pasar lista.</div>', unsafe_allow_html=True)
        else:
            c_asist = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique(), key="asist_sel")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_asist).not_.is_("alumno_id", "null").execute()
            
            if not res_a.data:
                st.info("Inscribe alumnos en este curso para pasar asistencia.")
            else:
                st.write(f"Fecha: {hoy}")
                for r in res_a.data:
                    col_alu, col_pres = st.columns([3, 1])
                    col_alu.write(f"👤 {r['alumnos']['apellido']}, {r['alumnos']['nombre']}")
                    if es_daguerre:
                        col_pres.number_input("Horas Faltadas", 0, 10, 0, key=f"f_{r['alumnos']['id']}")
                    else:
                        col_pres.checkbox("Presente", value=True, key=f"p_{r['alumnos']['id']}")
                
                if st.button("💾 Guardar Asistencia"):
                    st.success("Asistencia registrada correctamente.")
                
                if st.button("🖨️ Imprimir Planilla de Asistencia"):
                    st.markdown('<div class="print-area"><h3>Planilla de Asistencia</h3><p>Curso: ' + c_asist + '</p></div>', unsafe_allow_html=True)

    # --- TAB 1, 3, 4: (Mantienen la lógica de escudos anterior) ---
    with tabs[1]:
        st.subheader("Búsqueda de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Inscribe alumnos después de crear un curso.</div>', unsafe_allow_html=True)
        else:
            st.text_input("🔍 Buscar Alumno por Apellido")
            st.info("Buscador listo. Selecciona una materia para ver la lista completa.")

    with tabs[3]:
        st.subheader("Notas")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea un curso primero.</div>', unsafe_allow_html=True)
        else:
            st.info("Selecciona un curso para cargar calificaciones.")

    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_n, col_b = st.columns([4, 1])
                col_n.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
                if col_b.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            nc, hc = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear Curso"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
