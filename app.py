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
    .print-area { background-color: white; color: black; padding: 25px; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd; }
    @media print { .no-print { display: none !important; } .stApp { background-color: white !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
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
    hoy = datetime.datetime.now()
    es_daguerre = "daguerre" in user['email'].lower()
    
    st.sidebar.write(f"Sede: {'Daguerre' if es_daguerre else 'Cambridge'}")
    st.sidebar.write(f"Fecha: {hoy.strftime('%d/%m/%Y')}")
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

    # --- TAB ASISTENCIA (LÓGICA DAGUERRE/CAMBRIDGE) ---
    with tabs[2]:
        st.subheader("Control de Presentismo")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ <b>No hay cursos.</b> Ve a la pestaña Cursos para empezar.</div>', unsafe_allow_html=True)
        else:
            c_asist = st.selectbox("Elegir Curso:", df_cursos['nombre_curso_materia'].unique())
            st.write(f"📅 Clase del día: **{hoy.strftime('%A %d de %B')}**")
            
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_asist).not_.is_("alumno_id", "null").execute()
            
            if not res_a.data:
                st.info("Primero inscribe alumnos en este curso.")
            else:
                asistencia_data = []
                for r in res_a.data:
                    col1, col2 = st.columns([3, 1])
                    nombre_full = f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}"
                    col1.write(f"👤 {nombre_full}")
                    if es_daguerre:
                        valor = col2.number_input("Horas Faltas", 0, 10, 0, key=f"f_{r['alumnos']['id']}")
                        asistencia_data.append({"Alumno": nombre_full, "Faltas (Horas)": valor})
                    else:
                        valor = col2.checkbox("Presente", value=True, key=f"p_{r['alumnos']['id']}")
                        asistencia_data.append({"Alumno": nombre_full, "Estado": "Presente" if valor else "Ausente"})

                if st.button("🖨️ Imprimir Planilla de Hoy"):
                    st.markdown('<div class="print-area">', unsafe_allow_html=True)
                    st.write(f"### Planilla de Asistencia - {'Daguerre' if es_daguerre else 'Cambridge'}")
                    st.write(f"**Materia:** {c_asist} | **Fecha:** {hoy.strftime('%d/%m/%Y %H:%M')}")
                    st.table(pd.DataFrame(asistencia_data))
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- RESTO DE PESTAÑAS (MANTIENEN PROTECCIÓN) ---
    with tabs[1]:
        st.subheader("Búsqueda de Alumnos")
        if not df_cursos.empty:
            busq = st.text_input("🔍 Buscar por Apellido")
            st.info("Escribe para filtrar. Si la lista está vacía, inscribe alumnos abajo.")
        else:
            st.markdown('<div class="warning-card">⚠️ Crea un curso primero.</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.subheader("Mis Cursos")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                st.write(f"📘 {cur['nombre_curso_materia']} - {cur['horario']}")
        with st.form("n_c"):
            n, h = st.text_input("Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if n and h:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n, "horario": h, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # Agenda y Notas con cartel de guía
    for i, label in [(0, "Agenda"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            st.markdown(f'<div class="warning-card">📝 <b>Sección lista.</b> Selecciona un curso arriba para operar.</div>', unsafe_allow_html=True)
