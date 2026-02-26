import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

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

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ AUTOMÁTICO ---
components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; z-index:9999;">--:--:--</div>
    <script>
    function t(){
        const n=new Date();
        const h=String(n.getHours()).padStart(2,'0');
        const m=String(n.getMinutes()).padStart(2,'0');
        const s=String(n.getSeconds()).padStart(2,'0');
        document.getElementById('rtc').innerText=h+":"+m+":"+s;
    }
    setInterval(t,1000); t();
    </script>
    """, height=40)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v141"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res and res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Acceso denegado.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"Sede: {u_data['email'].split('.')[0].capitalize()}")
        st.divider()
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clases")
        if not mapa_cursos:
            st.info("ℹ️ No hay materias creadas. Ve a 'Cursos' para empezar.")
        else:
            sel_ag = st.selectbox("Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="v141_ag_sel")
            if sel_ag != "---":
                with st.form("f_ag_v141"):
                    f_hoy = datetime.date.today()
                    st.write(f"Registro: {f_hoy.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados")
                    f_tarea = st.date_input("Fecha tarea", value=f_hoy + datetime.timedelta(days=7))
                    desc_tarea = st.text_area("Descripción tarea")
                    c1, c2, c3 = st.columns(3)
                    if c1.form_submit_button("💾 GUARDAR"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": desc_tarea, "fecha_tarea": str(f_tarea)}).execute()
                        st.success("Guardado.")
                        st.rerun()
                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()

    # --- TAB 3: NOTAS (RESTABLECIDA CON FILTROS) ---
    with tabs[3]:
        st.subheader("📝 Gestión de Notas")
        if not mapa_cursos:
            st.info("ℹ️ Debe crear una materia primero.")
        else:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            n1, n2 = st.columns(2)
            f_n_cur = n1.selectbox("Curso:", ["Seleccione..."] + list(mapa_cursos.keys()), key="v141_nt_c")
            f_n_bus = n2.text_input("Buscar Apellido:", key="v141_nt_b").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if f_n_cur != "Seleccione...":
                r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_n_cur).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_n_bus in al['apellido'].lower():
                            with st.expander(f"📝 {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_nt_{al['id']}"):
                                    st.text_input("Nota")
                                    st.text_input("Instancia")
                                    c1, c2, c3 = st.columns(3)
                                    if c1.form_submit_button("💾 GUARDAR"): st.rerun()
                                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
                else: st.warning("No hay alumnos en este curso.")

    # --- TABS ALUMNOS, ASISTENCIA Y CURSOS (MANTENIDOS) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        f_m_al = col1.selectbox("Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v141_f_m_al")
        f_n_al = col2.text_input("Buscar Apellido:", key="v141_f_n_al").lower()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="v141_as_c")
            f_as_n = ac2.text_input("Buscar Alumno:", key="v141_as_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("crear_c_v141"):
            nc_nom = st.text_input("Nombre de Materia")
            if st.form_submit_button("💾 GRABAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc_nom, "anio_lectivo": 2026}).execute()
                st.rerun()
