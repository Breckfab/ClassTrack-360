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
        with st.form("login_v123"):
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
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("🚪 SALIR DEL SISTEMA"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (FILTROS POR MATERIA Y NOMBRE) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        c1, c2 = st.columns(2)
        f_al_mat = c1.selectbox("Filtrar por Materia:", ["Todas"] + list(mapa_cursos.keys()), key="al_mat")
        f_al_nom = c2.text_input("Buscar por Apellido/Nombre:", key="al_nom").lower()
        
        try:
            r_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for it in r_al.data:
                    al = it['alumnos']
                    if (f_al_mat == "Todas" or it['nombre_curso_materia'] == f_al_mat) and (f_al_nom in al['nombre'].lower() or f_al_nom in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                            with st.form(f"f_al_v123_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3) [cite: 2026-02-15]
                                if b1.form_submit_button("GUARDAR"): st.rerun()
                                if b2.form_submit_button("CANCELAR"): st.rerun()
                                if b3.form_submit_button("⚠️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: st.error("Error al cargar alumnos.")

    # --- TAB 2: ASISTENCIA (FILTROS POR MATERIA Y NOMBRE) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            ac1, ac2 = st.columns(2)
            f_as_mat = ac1.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="as_mat")
            f_as_nom = ac2.text_input("Buscar Apellido:", key="as_nom").lower()
            if f_as_mat != "--- Seleccionar ---":
                st.info(f"Mostrando lista para {f_as_mat}...")
        else: st.info("Cree una materia primero.")

    # --- TAB 3: NOTAS (FILTROS POR MATERIA Y NOMBRE) ---
    with tabs[3]:
        st.subheader("📝 Calificaciones")
        if mapa_cursos:
            nc1, nc2 = st.columns(2)
            f_nt_mat = nc1.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="nt_mat")
            f_nt_nom = nc2.text_input("Buscar Apellido:", key="nt_nom").lower()
            
            if f_nt_mat != "--- Seleccionar ---":
                r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_mat).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_nt_nom in al['apellido'].lower():
                            with st.expander(f"📝 {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_nt_v123_{al['id']}"):
                                    st.text_input("Nota")
                                    st.text_input("Instancia")
                                    nb1, nb2, nb3 = st.columns(3) [cite: 2026-02-15]
                                    if nb1.form_submit_button("GUARDAR"): st.rerun()
                                    if nb2.form_submit_button("CANCELAR"): st.rerun()
                                    if nb3.form_submit_button("BORRAR"): st.rerun()
                else: st.warning("⚠️ Sin alumnos en esta materia.")
        else: st.info("Cree una materia primero.")

    # --- TAB 0: AGENDA (FECHA VISIBLE) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            m_sel = st.selectbox("Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="ag_v123")
            if m_sel != "--- Seleccionar ---":
                with st.form("f_ag_v123"):
                    st.write(f"Registro del día: {datetime.date.today().strftime('%d/%m/%Y')}")
                    st.text_area("Temas dictados")
                    st.date_input("Próxima tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR"): st.rerun()

    # --- TAB 4: CURSOS (TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("🏗️ Materias")
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                with st.form(f"c_ed_v123_{i}"):
                    st.text_input("Materia", value=n)
                    cb1, cb2, cb3 = st.columns(3) [cite: 2026-02-15]
                    if cb1.form_submit_button("GUARDAR"): st.rerun()
                    if cb2.form_submit_button("CANCELAR"): st.rerun()
                    if cb3.form_submit_button("BORRAR"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
