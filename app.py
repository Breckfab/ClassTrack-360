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

# --- RELOJ ---
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
        with st.form("login_v139"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res and res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"Sede: {u_data['email'].split('.')[0].capitalize()}")
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

    # --- TAB 1: ALUMNOS (FILTROS RESTAURADOS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        # 1. Filtros siempre visibles
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        f_col1, f_col2 = st.columns(2)
        filtro_materia = f_col1.selectbox("📍 Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="f_m_al_v139")
        filtro_nombre = f_col2.text_input("🔍 Buscar por Apellido/Nombre:", key="f_n_al_v139").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Formulario de Inscripción
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("ins_al_v139"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Asignar a:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
                if st.form_submit_button("💾 REGISTRAR"):
                    res_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                        st.rerun()

        st.divider()

        # 3. Lista filtrada
        try:
            r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_l.data:
                for it in r_l.data:
                    al = it['alumnos']
                    if (filtro_materia == "Todas" or it['nombre_curso_materia'] == filtro_materia) and (filtro_nombre in al['nombre'].lower() or filtro_nombre in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} | {it['nombre_curso_materia']}"):
                            with st.form(f"ed_al_v139_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3) [cite: 2026-02-15]
                                if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                                if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if b3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
            else: st.info("No hay alumnos inscriptos.")
        except: pass

    # --- TAB 2: ASISTENCIA (FILTROS) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Curso:", ["Seleccione..."] + list(mapa_cursos.keys()), key="f_as_c_v139")
            f_as_n = ac2.text_input("Buscar Apellido:", key="f_as_n_v139").lower()
            st.markdown('</div>', unsafe_allow_html=True)
            if f_as_c != "Seleccione...":
                st.info(f"Mostrando alumnos de {f_as_c}")

    # --- TAB 3: NOTAS (FILTROS) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            nc1, nc2 = st.columns(2)
            f_nt_c = nc1.selectbox("Curso:", ["Seleccione..."] + list(mapa_cursos.keys()), key="f_nt_c_v139")
            f_nt_n = nc2.text_input("Alumno:", key="f_nt_n_v139").lower()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS (TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("crear_c_v139"):
            nc_nom = st.text_input("Nombre de Materia")
            if st.form_submit_button("💾 GRABAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc_nom, "anio_lectivo": 2026}).execute()
                st.rerun()
        st.divider()
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                with st.form(f"ops_c_v139_{i}"):
                    st.text_input("Nombre", value=n)
                    c1, c2, c3 = st.columns(3) [cite: 2026-02-15]
                    if c1.form_submit_button("💾 GUARDAR"): st.rerun()
                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if c3.form_submit_button("🗑️ BORRAR"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
