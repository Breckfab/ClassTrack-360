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

# --- ESTILO CSS Y RELOJ SUPERIOR DERECHO ---
ahora_server = datetime.datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp {{ background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }}
    
    /* RELOJ SUPERIOR DERECHO DISCRETO */
    .top-clock {{
        position: fixed;
        top: 10px;
        right: 20px;
        z-index: 9999;
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        color: #ffffff;
        font-weight: 400;
        background: rgba(0,0,0,0.2);
        padding: 5px 10px;
        border-radius: 5px;
    }}
    .logo-text {{ font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 15px; }}
    </style>
    
    <div class="top-clock" id="live-clock">{ahora_server}</div>

    <script>
    function updateClock() {{
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        const clockEl = document.getElementById('live-clock');
        if (clockEl) clockEl.innerText = h + ":" + m + ":" + s;
    }}
    setInterval(updateClock, 1000);
    </script>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v111"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                email = f"{{u_in}}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
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
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE DATOS ---
    mapa_cursos = {{}}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {{row['nombre_curso_materia']: row['id'] for row in r_c.data}}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA CON CALENDARIO) ---
    with tabs[0]:
        st.subheader("Agenda de Clases")
        if mapa_cursos:
            m_age = st.selectbox("Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v111")
            if m_age != "--- Seleccionar ---":
                with st.form("f_age_v111"):
                    t1 = st.text_area("¿Qué se dio hoy?")
                    st.write("📅 **Fecha de entrega de tarea**")
                    f_tar = st.date_input("Calendario", value=datetime.date.today())
                    t2 = st.text_area("Tarea para el alumno")
                    if st.form_submit_button("GUARDAR"):
                        supabase.table("bitacora").insert({{
                            "inscripcion_id": mapa_cursos[m_age], 
                            "fecha": str(datetime.date.today()), 
                            "contenido_clase": t1, 
                            "tarea_proxima": t2,
                            "fecha_tarea": str(f_tar)
                        }}).execute()
                        st.rerun()
        else: st.info("ℹ️ No hay cursos creados.")

    # --- TAB 4: CURSOS (LISTA ARRIBA Y TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_v111_{{i}}"):
                        new_name = st.text_input("Corregir Nombre", value=n)
                        c1, c2, c3 = st.columns(3) [cite: 2026-02-15]
                        if c1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({{"nombre_curso_materia": new_name}}).eq("id", i).execute()
                            st.rerun()
                        if c2.form_submit_button("CANCELAR"): st.rerun()
                        if c3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        st.divider()
        with st.form("f_new_c_v111"):
            st.write("### ➕ Nueva Materia")
            nc = st.text_input("Nombre")
            if st.form_submit_button("AGREGAR"):
                supabase.table("inscripciones").insert({{"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}}).execute()
                st.rerun()
