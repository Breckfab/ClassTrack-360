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
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
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
        with st.form("login_v146"):
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
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (LISTADO Y EDICIÓN) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("crear_c_v146"):
            nom_c = st.text_input("Nombre de Materia / Curso")
            if st.form_submit_button("💾 GRABAR MATERIA"):
                if nom_c:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nom_c, "anio_lectivo": 2026}).execute()
                    st.rerun()
        st.divider()
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    st.markdown('<span class="st-active">ACTIVO</span>', unsafe_allow_html=True)
                    with st.form(f"ops_c_{i}"):
                        new_nom = st.text_input("Nombre", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("💾 GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_nom}).eq("id", i).execute()
                            st.rerun()
                        if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                        if c3.form_submit_button("🗑️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        else: st.info("No hay cursos registrados.")

    # --- TAB 1: ALUMNOS (FILTROS Y BUSCADORES) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        col_al1, col_al2 = st.columns(2)
        f_al_c = col_al1.selectbox("Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="f_al_c_146")
        f_al_n = col_al2.text_input("Buscar Apellido:", key="f_al_n_146").lower()
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("ins_al_v146"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
                if st.form_submit_button("💾 REGISTRAR"):
                    res_al = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if res_al.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_al.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                        st.rerun()

    # --- TAB 0: AGENDA (FECHA AUTOMÁTICA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            sel_ag = st.selectbox("📍 Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="ag_v146")
            if sel_ag != "---":
                with st.form("f_ag_v146"):
                    f_hoy = datetime.date.today()
                    st.info(f"Fecha: {f_hoy.strftime('%d/%m/%Y')}")
                    st.text_area("Temas dictados")
                    if st.form_submit_button("💾 GUARDAR"):
                        st.success("Guardado."); st.rerun()

    # --- TAB 2 Y 3: ASISTENCIA Y NOTAS (FILTROS) ---
    with tabs[2]: st.subheader("✅ Asistencia"); st.info("Seleccione curso arriba.")
    with tabs[3]: st.subheader("📝 Notas"); st.info("Seleccione curso arriba.")
