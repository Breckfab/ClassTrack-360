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
    .print-area { background-color: white; color: black; padding: 25px; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd; }
    @media print { .no-print { display: none !important; } .stApp { background-color: white !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (BLINDADO PARA ENTER) ---
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
    es_daguerre = "daguerre" in user['email'].lower()
    
    st.sidebar.write(f"Sesión: {'Daguerre' if es_daguerre else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA MAESTRA DE CURSOS ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (RECUPERADA Y COMPLETA) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Tareas")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias. Crea una en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia de hoy:", df_cursos['nombre_curso_materia'].unique())
            c_info = df_cursos[df_cursos['nombre_curso_materia'] == c_agenda].iloc[0]
            
            # Recordatorio de tarea para hoy
            st.markdown('<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>Verifica si los alumnos trajeron lo solicitado la clase pasada.</div>', unsafe_allow_html=True)
            
            with st.form("form_agenda_completa"):
                temas = st.text_area("Contenidos dictados hoy:")
                tarea_sig = st.text_area("Tarea para la próxima clase:")
                f_venc = st.date_input("Fecha de entrega (Recordatorio):", hoy + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar en Bitácora"):
                    if temas:
                        st.success(f"Clase de {c_agenda} guardada correctamente.")
                    else: st.warning("Por favor describe lo dictado hoy.")

    # --- TAB 1: ALUMNOS (CON BUSCADOR E INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("Búsqueda e Inscripción")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Primero crea una materia en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            busq_alu = st.text_input("🔍 Buscar Alumno por Apellido")
            with st.expander("➕ Inscribir Estudiante", expanded=False):
                with st.form("ins_alu_f"):
                    c_sel = st.selectbox("Asignar a:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
                    nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        st.success("Alumno anotado."); st.rerun()

    # --- TAB 2: ASISTENCIA (HORAS O PRESENTE) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea un curso primero.</div>', unsafe_allow_html=True)
        else:
            c_asist = st.selectbox("Elegir materia:", df_cursos['nombre_curso_materia'].unique(), key="as_sel")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_asist).not_.is_("alumno_id", "null").execute()
            
            if not res_a.data:
                st.markdown('<div class="warning-card">⚠️ No hay alumnos inscritos aún en este curso.</div>', unsafe_allow_html=True)
            else:
                asist_list = []
                for r in res_a.data:
                    col1, col2 = st.columns([3, 1])
                    nombre = f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}"
                    col1.write(f"👤 {nombre}")
                    if es_daguerre:
                        h = col2.number_input("Horas Faltas", 0, 10, 0, key=f"f_{r['alumnos']['id']}")
                        asist_list.append({"Alumno": nombre, "Faltas": f"{h} hs"})
                    else:
                        p = col2.checkbox("Presente", value=True, key=f"p_{r['alumnos']['id']}")
                        asist_list.append({"Alumno": nombre, "Estado": "Presente" if p else "Ausente"})
                
                if st.button("🖨️ Imprimir Planilla de Asistencia"):
                    st.markdown('<div class="print-area">', unsafe_allow_html=True)
                    st.write(f"### Asistencia {hoy.strftime('%d/%m/%Y')} - {c_asist}")
                    st.table(pd.DataFrame(asist_list))
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 3: NOTAS (PROMEDIOS E IMPRESIÓN) ---
    with tabs[3]:
        st.subheader("Planilla de Calificaciones")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea un curso primero.</div>', unsafe_allow_html=True)
        else:
            c_notas = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="nt_sel")
            res_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_notas).not_.is_("alumno_id", "null").execute()
            
            if not res_n.data:
                st.markdown('<div class="warning-card">⚠️ No hay alumnos registrados aún para mostrar notas.</div>', unsafe_allow_html=True)
            else:
                notas_data = [{"Alumno": f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}", "Nota 1": 0.0, "Nota 2": 0.0, "Promedio": 0.0} for r in res_n.data]
                st.data_editor(pd.DataFrame(notas_data), use_container_width=True)
                if st.button("🖨️ Generar Acta para Imprimir"):
                    st.markdown('<div class="print-area"><h3>Acta de Notas</h3></div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("n_c_f"):
            nc, hc = st.text_input("Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear Materia"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
