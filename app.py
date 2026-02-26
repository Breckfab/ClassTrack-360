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

# --- ESTILO CSS (ETIQUETAS Y LOGO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 8px; border-radius: 4px; background: rgba(255,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v102"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res and res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA CRÍTICA (ESTRUCTURA DE MATERIAS) ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RECUPERADA Y BLINDADA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if mapa_cursos:
            m_age = st.selectbox("Seleccionar Materia:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_age_v102")
            if m_age != "--- Elegir ---":
                with st.form("f_new_bit_v102"):
                    t1 = st.text_area("Contenido dictado")
                    t2 = st.text_area("Tarea para la próxima")
                    if st.form_submit_button("GUARDAR CLASE"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_age], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                        st.rerun()
        else: st.info("ℹ️ Para registrar clases, primero cree una materia en 'Cursos'.")

    # --- TAB 2: ASISTENCIA (RECUPERADA Y BLINDADA) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if mapa_cursos:
            m_as = st.selectbox("Elegir Materia:", list(mapa_cursos.keys()), key="sb_as_v102")
            # Mostrar formulario de toma siempre
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
            if r_as.data:
                with st.form("f_as_v102"):
                    checks = []
                    for it in r_as.data:
                        al = it['alumnos']
                        est = st.radio(f"{al['apellido']}, {al['nombre']}", ["Presente", "Ausente"], key=f"as_v102_{al['id']}", horizontal=True)
                        checks.append({"id": al['id'], "est": est})
                    if st.form_submit_button("GUARDAR ASISTENCIA"):
                        for c in checks:
                            supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                        st.success("✅ Asistencia guardada.")
            else: st.info("ℹ️ No hay alumnos inscriptos para tomar asistencia.")
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 3: NOTAS (RECUPERADA Y BLINDADA) ---
    with tabs[3]:
        st.subheader("Gestión de Calificaciones")
        if mapa_cursos:
            m_nt = st.selectbox("Elegir Materia:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_nt_v102")
            if m_nt != "--- Elegir ---":
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if r_al_n.data:
                    for item in r_al_n.data:
                        al = item['alumnos']
                        with st.expander(f"📝 Notas de {al['apellido']}, {al['nombre']}"):
                            with st.form(f"f_nota_{al['id']}"):
                                val_n = st.text_input("Calificación")
                                des_n = st.text_input("Instancia (Examen, TP...)")
                                if st.form_submit_button("REGISTRAR NOTA"):
                                    supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": m_nt, "nota": val_n, "descripcion": des_n, "fecha": str(ahora.date())}).execute()
                                    st.rerun()
                else: st.info("ℹ️ No hay alumnos en esta materia.")
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 1 y 4 (ALUMNOS Y CURSOS) ---
    with tabs[1]: st.info("ℹ️ Use el buscador o inscriba alumnos nuevos aquí.")
    with tabs[4]: 
        st.subheader("Configuración de Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    if st.button(f"BORRAR CURSO {n}", key=f"bc_v102_{i}"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
        st.divider()
        with st.form("f_c_v102"):
            nc = st.text_input("Nueva Materia")
            if st.form_submit_button("GUARDAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
