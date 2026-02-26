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

# --- ESTILO Y RELOJ SUPERIOR DERECHO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; font-weight:400; z-index:9999;">--:--:--</div>
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
        with st.form("login_v124"):
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
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (FILTROS SIEMPRE VISIBLES) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_al_c = c1.selectbox("📍 Filtrar por Materia/Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v124_f_al_c")
        f_al_n = c2.text_input("🔍 Buscar por Nombre o Apellido:", key="v124_f_al_n").lower()
        st.markdown('</div>', unsafe_allow_html=True)
        
        try:
            r_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for it in r_al.data:
                    al = it['alumnos']
                    if (f_al_c == "Todas" or it['nombre_curso_materia'] == f_al_c) and (f_al_n in al['nombre'].lower() or f_al_n in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                            with st.form(f"ed_al_v124_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                bc1, bc2, bc3 = st.columns(3) [cite: 2026-02-15]
                                if bc1.form_submit_button("GUARDAR"): st.rerun()
                                if bc2.form_submit_button("CANCELAR"): st.rerun()
                                if bc3.form_submit_button("⚠️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: st.error("Error al cargar lista.")

    # --- TAB 3: NOTAS (FILTROS SIEMPRE VISIBLES) ---
    with tabs[3]:
        st.subheader("📝 Gestión de Notas")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        nc1, nc2 = st.columns(2)
        f_nt_c = nc1.selectbox("📍 Elegir Materia/Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="v124_f_nt_c")
        f_nt_n = nc2.text_input("🔍 Buscar Alumno (Apellido):", key="v124_f_nt_n").lower()
        st.markdown('</div>', unsafe_allow_html=True)
        
        if f_nt_c != "--- Seleccionar ---":
            r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_c).not_.is_("alumno_id", "null").execute()
            if r_nt.data:
                for it in r_nt.data:
                    al = it['alumnos']
                    if f_nt_n in al['apellido'].lower():
                        with st.expander(f"📝 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"f_nt_v124_{al['id']}"):
                                st.text_input("Nota")
                                st.text_input("Instancia")
                                n1, n2, n3 = st.columns(3) [cite: 2026-02-15]
                                if n1.form_submit_button("GUARDAR"): st.rerun()
                                if n2.form_submit_button("CANCELAR"): st.rerun()
                                if n3.form_submit_button("BORRAR"): st.rerun()
            else: st.warning("⚠️ Sin alumnos en esta materia.")

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("📅 Registro de Clase")
        if mapa_cursos:
            m_a = st.selectbox("Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="age_v124")
            if m_a != "--- Elegir ---":
                with st.form("f_ag_v124"):
                    st.write(f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}")
                    st.text_area("Temas")
                    st.date_input("Fecha tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR"): st.rerun()

    # --- TAB 4: CURSOS (ORDEN INVERSO) ---
    with tabs[4]:
        st.subheader("🏗️ Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"c_ed_v124_{i}"):
                        st.text_input("Nombre", value=n)
                        b1, b2, b3 = st.columns(3) [cite: 2026-02-15]
                        if b1.form_submit_button("GUARDAR"): st.rerun()
                        if b2.form_submit_button("CANCELAR"): st.rerun()
                        if b3.form_submit_button("BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
