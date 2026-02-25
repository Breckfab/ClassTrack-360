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
    .print-area { background-color: white; color: black; padding: 20px; border-radius: 10px; margin-top: 20px; }
    @media print {
        .no-print { display: none !important; }
        .stApp { background-color: white !important; color: black !important; }
    }
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

    # Carga base de datos
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 3: NOTAS (FILTROS, PROMEDIOS E IMPRESIÓN) ---
    with tabs[3]:
        st.subheader("Planilla de Calificaciones")
        if not df_cursos.empty:
            col_n1, col_n2 = st.columns([2, 1])
            curso_n = col_n1.selectbox("Seleccionar Curso para Notas", df_cursos['nombre_curso_materia'].unique())
            anio_n = col_n2.selectbox("Año", sorted(df_cursos['anio_lectivo'].unique(), reverse=True), key="n_anio")

            # Obtener alumnos del curso
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", curso_n).eq("anio_lectivo", anio_n).not_.is_("alumno_id", "null").execute()
            
            if res_a.data:
                # Simulación de carga de notas (esto se conectará a la tabla 'notas' en el siguiente paso)
                # Por ahora, armamos la estructura de la planilla para impresión
                data_notas = []
                for r in res_a.data:
                    data_notas.append({
                        "Alumno": f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}",
                        "Nota 1": 0.0,
                        "Nota 2": 0.0,
                        "Promedio": 0.0
                    })
                
                df_notas = pd.DataFrame(data_notas)
                st.data_editor(df_notas, use_container_width=True, disabled=["Alumno", "Promedio"], key="editor_notas")
                
                st.divider()
                if st.button("🖨️ Generar Acta de Notas para Imprimir"):
                    st.markdown('<div class="print-area">', unsafe_allow_html=True)
                    st.markdown(f"## Acta de Calificaciones - {curso_n}")
                    st.markdown(f"**Docente:** {user['email']} | **Año Lectivo:** {anio_n}")
                    st.table(df_notas)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.info("💡 Presioná Ctrl+P para imprimir esta acta.")
            else:
                st.info("No hay alumnos inscritos en este curso para calificar.")
        else:
            st.info("Cargá una materia en 'Cursos' para habilitar las notas.")

    # --- TAB 1: ALUMNOS (FILTROS) ---
    with tabs[1]:
        st.subheader("Búsqueda de Alumnos")
        if not df_cursos.empty:
            busq = st.text_input("🔍 Buscar por apellido")
            # Mostrar tabla filtrada... (Mantenemos la lógica anterior)
            st.write("Escribe el apellido para filtrar la lista.")
        else:
            st.info("Sin cursos registrados.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_n, col_b = st.columns([4, 1])
                col_n.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
                if col_b.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            st.write("➕ Añadir Materia")
            nc = st.text_input("Nombre")
            hc = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # Pestañas pendientes
    with tabs[0]: st.subheader("Agenda"); st.info("Registro de clases disponible al seleccionar curso.")
    with tabs[2]: st.subheader("Asistencia"); st.info("Control de presentismo por curso.")
