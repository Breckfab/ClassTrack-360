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
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
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
        with st.form("login_v121"):
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
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (FILTROS CRUZADOS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        col_f1, col_f2 = st.columns(2)
        filtro_curso_al = col_f1.selectbox("Filtrar por Curso:", ["Todos"] + list(mapa_cursos.keys()), key="f_c_al")
        bus_nom_al = col_f2.text_input("Buscar por Nombre/Apellido:", key="b_n_al").lower()
        
        try:
            r_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for item in r_al.data:
                    alu = item['alumnos']
                    cumple_curso = (filtro_curso_al == "Todos" or item['nombre_curso_materia'] == filtro_curso_al)
                    cumple_nombre = (bus_nom_al in alu['nombre'].lower() or bus_nom_al in alu['apellido'].lower())
                    
                    if cumple_curso and cumple_nombre:
                        with st.expander(f"👤 {alu['apellido'].upper()}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                            with st.form(f"ed_alu_v121_{item['id']}"):
                                n_n = st.text_input("Nombre", value=alu['nombre'])
                                n_a = st.text_input("Apellido", value=alu['apellido'])
                                n_c = st.selectbox("Cambiar Curso:", list(mapa_cursos.keys()), index=list(mapa_cursos.keys()).index(item['nombre_curso_materia']) if item['nombre_curso_materia'] in mapa_cursos else 0)
                                c1, c2, c3 = st.columns(3) [cite: 2026-02-15]
                                if c1.form_submit_button("💾 GUARDAR"):
                                    supabase.table("alumnos").update({"nombre": n_n, "apellido": n_a}).eq("id", alu['id']).execute()
                                    if n_c != item['nombre_curso_materia']:
                                        supabase.table("inscripciones").update({"nombre_curso_materia": n_c}).eq("id", item['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if c3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", item['id']).execute()
                                    st.rerun()
            else: st.info("No hay alumnos.")
        except: st.error("Error al cargar lista.")

    # --- TAB 2: ASISTENCIA (FILTROS CRUZADOS) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            cf1, cf2 = st.columns(2)
            f_c_as = cf1.selectbox("Curso:", list(mapa_cursos.keys()), key="f_c_as")
            f_n_as = cf2.text_input("Apellido:", key="f_n_as").lower()
            st.info(f"Buscando en {f_c_as}...")
        else: st.warning("Cree una materia primero.")

    # --- TAB 3: NOTAS (FILTROS CRUZADOS Y EDICIÓN) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            nf1, nf2 = st.columns(2)
            f_c_nt = nf1.selectbox("Curso:", list(mapa_cursos.keys()), key="f_c_nt")
            f_n_nt = nf2.text_input("Apellido:", key="f_n_nt").lower()
            
            r_nt = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_c_nt).not_.is_("alumno_id", "null").execute()
            if r_nt.data:
                for item in r_nt.data:
                    al = item['alumnos']
                    if f_n_nt in al['apellido'].lower():
                        with st.expander(f"📝 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"add_nt_{al['id']}"):
                                v_n = st.text_input("Nota")
                                v_d = st.text_input("Instancia")
                                b1, b2, b3 = st.columns(3) [cite: 2026-02-15]
                                if b1.form_submit_button("GUARDAR"):
                                    supabase.table("notas").insert({"alumno_id": al['id'], "materia": f_c_nt, "nota": v_n, "descripcion": v_d}).execute()
                                    st.rerun()
                                if b2.form_submit_button("CANCELAR"): st.rerun()
                                if b3.form_submit_button("BORRAR"): st.rerun()
            else: st.info("No hay alumnos en este curso.")
        else: st.warning("Sin materias.")

    # --- TAB 0: AGENDA (CON FECHA VISIBLE) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            m_a = st.selectbox("Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="age_v121")
            if m_a != "--- Elegir ---":
                with st.form("f_a_v121"):
                    f_c = st.date_input("Fecha Clase", value=datetime.date.today())
                    tem = st.text_area(f"Dictado el {f_c.strftime('%d/%m/%Y')}")
                    f_t = st.date_input("Fecha Tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    tar = st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_a], "fecha": str(f_c), "contenido_clase": tem, "tarea_proxima": tar, "fecha_tarea": str(f_t)}).execute()
                        st.rerun()
        else: st.info("Cree una materia primero.")
