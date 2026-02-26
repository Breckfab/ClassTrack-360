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
        with st.form("login_v120"):
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

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON FECHA VISIBLE) ---
    with tabs[0]:
        st.subheader("📅 Registro de Clase")
        if mapa_cursos:
            m_age = st.selectbox("Seleccionar Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="age_sel_v120")
            if m_age != "--- Seleccionar ---":
                with st.form("f_agenda_v120"):
                    fecha_hoy_str = datetime.date.today().strftime("%d/%m/%Y")
                    # Se agrega la fecha visualmente en el título del campo
                    st.write(f"📅 **Fecha de hoy:** {fecha_hoy_str}")
                    
                    f_clase = st.date_input("Fecha de la clase registrada", value=datetime.date.today())
                    temas = st.text_area(f"Temas dictados el {f_clase.strftime('%d/%m/%Y')}")
                    
                    st.divider()
                    st.write("📌 **Tarea próxima clase**")
                    f_entrega = st.date_input("Fecha de entrega de tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    tarea_desc = st.text_area("Descripción de la tarea")
                    
                    c1, c2, c3 = st.columns(3)
                    if c1.form_submit_button("💾 GUARDAR"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_age],
                            "fecha": str(f_clase), # Guarda la fecha seleccionada por el profesor
                            "contenido_clase": temas,
                            "tarea_proxima": tarea_desc,
                            "fecha_tarea": str(f_entrega)
                        }).execute()
                        st.success(f"✅ Clase del {f_clase.strftime('%d/%m/%Y')} guardada.")
                        st.rerun()
                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
        else: st.warning("Debe crear una materia en 'Cursos' primero.")

    # --- TAB 1: ALUMNOS (SIN CAMBIOS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        bus_alu = st.text_input("🔍 Buscar por nombre o apellido...", key="bus_alu_v120").lower()
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu and (bus_alu in alu['nombre'].lower() or bus_alu in alu['apellido'].lower()):
                        with st.expander(f"👤 {alu['apellido'].upper()}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                            with st.form(f"ed_alu_{item['id']}"):
                                n_n = st.text_input("Nombre", value=alu['nombre'])
                                n_a = st.text_input("Apellido", value=alu['apellido'])
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("💾 GUARDAR"):
                                    supabase.table("alumnos").update({"nombre": n_n, "apellido": n_a}).eq("id", alu['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if c3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", item['id']).execute()
                                    st.rerun()
        except: st.error("Error al cargar alumnos.")

    # --- TABS ASISTENCIA, NOTAS Y CURSOS (SIN CAMBIOS) ---
    with tabs[2]: st.subheader("✅ Asistencia"); st.info("Buscador de asistencia disponible.")
    with tabs[3]: st.subheader("📝 Notas"); st.info("Buscador de notas disponible.")
    with tabs[4]:
        st.subheader("🏗️ Materias")
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                with st.form(f"ed_c_v120_{i}"):
                    st.text_input("Nombre", value=n)
                    b1, b2, b3 = st.columns(3)
                    if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                    if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if b3.form_submit_button("🗑️ BORRAR"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
