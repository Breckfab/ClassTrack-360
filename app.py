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

# --- ESTILO CSS Y RELOJ JAVASCRIPT ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono:wght@500&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .clock-container { font-family: 'JetBrains Mono', monospace; font-size: 2rem; color: #00f2fe; text-align: center; background: rgba(0,0,0,0.4); padding: 15px; border-radius: 12px; border: 2px solid #4facfe; margin-bottom: 25px; box-shadow: 0 0 20px rgba(79, 172, 254, 0.3); }
    </style>
    
    <div class="clock-container" id="clock">00:00:00</div>

    <script>
    function updateClock() {
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        document.getElementById('clock').innerText = h + ":" + m + ":" + s;
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v107"):
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
        if st.button("SALIR DEL SISTEMA"):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON CALENDARIO RESTAURADO) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Tareas")
        if mapa_cursos:
            m_age = st.selectbox("Elegir Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v107")
            if m_age != "--- Seleccionar ---":
                with st.form("f_age_v107"):
                    t1 = st.text_area("Temas dictados")
                    st.write("📅 **Programar Tarea**")
                    f_tar = st.date_input("Fecha de entrega", value=datetime.date.today())
                    t2 = st.text_area("Detalle de la tarea")
                    if st.form_submit_button("GUARDAR REGISTRO COMPLETO"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_age], 
                            "fecha": str(datetime.date.today()), 
                            "contenido_clase": t1, 
                            "tarea_proxima": t2,
                            "fecha_tarea": str(f_tar)
                        }).execute()
                        st.rerun()
        else: st.info("ℹ️ Sin materias creadas.")

    # --- TAB 3: NOTAS (CON LEYENDAS Y TRIPLE BOTONERA) ---
    with tabs[3]:
        st.subheader("Gestión de Calificaciones")
        if mapa_cursos:
            m_nt = st.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_nt_v107")
            if m_nt != "--- Seleccionar ---":
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if not r_al_n.data:
                    st.error("❌ No hay alumnos para mostrar.")
                else:
                    for item in r_al_n.data:
                        al = item['alumnos']
                        with st.expander(f"📝 Notas: {al['apellido']}, {al['nombre']}"):
                            # Triple botonera para notas existentes
                            r_ex = supabase.table("notas").select("*").eq("alumno_id", al['id']).eq("materia", m_nt).execute()
                            if r_ex.data:
                                for nt in r_ex.data:
                                    with st.form(f"ed_nt_{nt['id']}"):
                                        st.text_input("Nota", value=nt['nota'])
                                        st.text_input("Instancia", value=nt['descripcion'])
                                        c1, c2, c3 = st.columns(3)
                                        if c1.form_submit_button("GUARDAR"): st.rerun()
                                        if c2.form_submit_button("CANCELAR"): st.rerun()
                                        if c3.form_submit_button("⚠️ BORRAR"):
                                            supabase.table("notas").delete().eq("id", nt['id']).execute()
                                            st.rerun()
                            else: st.warning("⚠️ Sin notas cargadas.")
        else: st.info("ℹ️ Cree una materia primero.")

    # --- TAB 4: CURSOS (CON EDICIÓN) ---
    with tabs[4]:
        st.subheader("Configuración de Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_cur_{i}"):
                        new_n = st.text_input("Nombre", value=n)
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_n}).eq("id", i).execute()
                            st.rerun()
                        if b2.form_submit_button("CANCELAR"): st.rerun()
                        if b3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
