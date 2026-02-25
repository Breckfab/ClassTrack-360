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
    .warning-card { 
        background: rgba(255, 184, 0, 0.1); 
        border-left: 5px solid #ffb800; 
        padding: 20px; 
        border-radius: 10px; 
        margin: 10px 0;
        color: #ffb800;
    }
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
    st.sidebar.write(f"Sede activa")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA BASE DE DATOS ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 3: NOTAS (CON PROTECCIÓN Y ADVERTENCIAS) ---
    with tabs[3]:
        st.subheader("Planilla de Calificaciones")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>No hay cursos creados.</b><br>Primero debes ir a la pestaña <b>Cursos</b> y añadir una materia para poder cargar notas.</div>', unsafe_allow_html=True)
        else:
            col_n1, col_n2 = st.columns([2, 1])
            curso_n = col_n1.selectbox("Seleccionar Curso:", df_cursos['nombre_curso_materia'].unique())
            anio_n = col_n2.selectbox("Año Lectivo:", sorted(df_cursos['anio_lectivo'].unique(), reverse=True))

            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", curso_n).eq("anio_lectivo", anio_n).not_.is_("alumno_id", "null").execute()
            
            if not res_a.data:
                st.markdown(f'<div class="warning-card">⚠️ <b>No hay alumnos inscritos en {curso_n}.</b><br>Para ver la planilla de notas, primero debes inscribir alumnos en este curso desde la pestaña <b>Alumnos</b>.</div>', unsafe_allow_html=True)
            else:
                data_notas = [{"Alumno": f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}", "Nota 1": 0.0, "Nota 2": 0.0, "Promedio": 0.0} for r in res_a.data]
                df_notas = pd.DataFrame(data_notas)
                st.data_editor(df_notas, use_container_width=True, disabled=["Alumno", "Promedio"])
                
                if st.button("🖨️ Generar Acta de Notas para Imprimir"):
                    st.markdown('<div class="print-area">', unsafe_allow_html=True)
                    st.markdown(f"## Acta de Calificaciones - {curso_n}")
                    st.markdown(f"**Institución:** {'Cambridge' if 'cambridge' in user['email'] else 'Daguerre'} | **Año:** {anio_n}")
                    st.table(df_notas)
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 1: ALUMNOS (CON PROTECCIÓN) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>¡Atención Profe!</b><br>Para poder inscribir alumnos, primero necesitas crear una materia en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            col_f1, col_f2 = st.columns([2, 1])
            busq = col_f1.text_input("🔍 Buscar Alumno por Apellido")
            curso_f = col_f2.selectbox("Filtrar por Materia:", ["Todas"] + list(df_cursos['nombre_curso_materia'].unique()))
            
            st.info("Escribe el nombre arriba para buscar o usa el botón de abajo para añadir uno nuevo.")
            with st.expander("➕ Inscribir Nuevo Estudiante"):
                with st.form("nuevo_alu_form", clear_on_submit=True):
                    c_ins = st.selectbox("Materia:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
                    n_a, a_a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n_a and a_a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n_a, "apellido": a_a}).execute()
                            c_nom, c_hor = c_ins.split(" | ")
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_nom, "horario": c_hor, "anio_lectivo": 2026}).execute()
                            st.success("Alumno inscrito."); st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Configuración de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_n, col_b = st.columns([4, 1])
                col_n.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
                if col_b.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            st.write("➕ Añadir Materia")
            nc, hc = st.text_input("Nombre de Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear Curso"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # Mensajes informativos para Agenda y Asistencia
    for i, label in [(0, "Agenda"), (2, "Asistencia")]:
        with tabs[i]:
            st.subheader(label)
            st.markdown(f'<div class="warning-card">📝 <b>Sección en preparación.</b><br>Primero asegúrate de tener cursos y alumnos cargados.</div>', unsafe_allow_html=True)
