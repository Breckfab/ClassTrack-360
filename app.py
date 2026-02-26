import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v127", layout="wide")

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

# --- RELOJ SUPERIOR DERECHO ---
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
        with st.form("login_v127"):
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
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (CORREGIDA) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Seleccionar Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="f_as_c")
            f_as_n = ac2.text_input("Buscar Alumno:", key="f_as_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if f_as_c != "--- Seleccionar ---":
                r_as = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_as_c).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    for it in r_as.data:
                        al = it['alumnos']
                        if f_as_n in al['apellido'].lower() or f_as_n in al['nombre'].lower():
                            with st.expander(f"📌 {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_as_{al['id']}"):
                                    estado = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                    c1, c2, c3 = st.columns(3)
                                    if c1.form_submit_button("💾 GUARDAR"):
                                        supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": f_as_c, "estado": estado, "fecha": str(datetime.date.today())}).execute()
                                        st.success("Asistencia guardada")
                                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
                else: st.info("No hay alumnos en este curso.")
        else: st.warning("Cree un curso primero.")

    # --- TAB 3: NOTAS (CORREGIDA) ---
    with tabs[3]:
        st.subheader("📝 Carga de Notas")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            nc1, nc2 = st.columns(2)
            f_nt_c = nc1.selectbox("Seleccionar Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="f_nt_c")
            f_nt_n = nc2.text_input("Buscar por Apellido:", key="f_nt_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if f_nt_c != "--- Seleccionar ---":
                r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_c).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_nt_n in al['apellido'].lower():
                            with st.expander(f"📝 NOTA PARA: {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_nota_{al['id']}"):
                                    v_nota = st.text_input("Nota (Ej: 9)")
                                    v_inst = st.text_input("Instancia (Ej: Parcial 1)")
                                    bc1, bc2, bc3 = st.columns(3)
                                    if bc1.form_submit_button("💾 GUARDAR"):
                                        supabase.table("notas").insert({"alumno_id": al['id'], "materia": f_nt_c, "nota": v_nota, "descripcion": v_inst}).execute()
                                        st.success("Nota registrada")
                                    if bc2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if bc3.form_submit_button("🗑️ BORRAR"): st.rerun()
        else: st.info("Cree un curso primero.")

    # --- TAB 1: ALUMNOS (INSCRIBIR Y EDITAR) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("n_alu"):
                nn = st.text_input("Nombre")
                na = st.text_input("Apellido")
                nc = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    res = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if res.data:
                        supabase.table("inscripciones").insert({"alumno_id": res.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc}).execute()
                        st.rerun()

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            m_a = st.selectbox("Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="ag_v127")
            if m_a != "--- Seleccionar ---":
                with st.form("f_ag"):
                    st.write(f"Hoy: {datetime.date.today().strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas de hoy")
                    if st.form_submit_button("💾 GUARDAR"): st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("n_cur"):
            nc_n = st.text_input("Nueva Materia")
            if st.form_submit_button("➕ CREAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc_n}).execute()
                st.rerun()
