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

# --- ESTILO CSS Y RELOJ SUPERIOR DERECHO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 8px; border-radius: 4px; background: rgba(255,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# Inyección de reloj blanco y discreto (automático)
components.html("""
    <div id="rtc" style="position:fixed; top:8px; right:20px; font-family:'JetBrains Mono',monospace; font-size:1.1rem; color:white; font-weight:400; z-index:9999;">00:00:00</div>
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
        with st.form("login_v114"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR"):
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

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if mapa_cursos:
            m_age = st.selectbox("Materia:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_age_v114")
            if m_age != "--- Elegir ---":
                with st.form("f_age_v114"):
                    t1 = st.text_area("Contenido")
                    f_tar = st.date_input("Fecha Tarea", value=datetime.date.today())
                    t2 = st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_age], "fecha": str(datetime.date.today()), "contenido_clase": t1, "tarea_proxima": t2, "fecha_tarea": str(f_tar)}).execute()
                        st.rerun()
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu:
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                            st.markdown(f"Estado: <span class='status-active'>{alu['estado']}</span>", unsafe_allow_html=True)
                            with st.form(f"ed_al_{alu['id']}"):
                                st.text_input("Nombre", value=alu['nombre'])
                                st.text_input("Apellido", value=alu['apellido'])
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("GUARDAR"): st.rerun()
                                if c2.form_submit_button("CANCELAR"): st.rerun()
                                if c3.form_submit_button("⚠️ BORRAR"):
                                    supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: st.error("Error al cargar alumnos.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if mapa_cursos:
            m_as = st.selectbox("Elegir Curso:", list(mapa_cursos.keys()), key="sb_as_v114")
            st.info(f"Registro para {m_as} disponible.")
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Calificaciones")
        if mapa_cursos:
            m_nt = st.selectbox("Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_nt_v114")
            if m_nt != "--- Elegir ---":
                st.info("ℹ️ Sin registros de notas.")
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_c_{i}"):
                        st.text_input("Nombre", value=n)
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("GUARDAR"): st.rerun()
                        if b2.form_submit_button("CANCELAR"): st.rerun()
                        if b3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        st.divider()
        with st.form("f_new_c"):
            nc = st.text_input("Nueva Materia")
            if st.form_submit_button("AGREGAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
