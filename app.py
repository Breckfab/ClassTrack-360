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

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .st-inactive { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; background: rgba(255,75,75,0.1); }
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ AUTOMÁTICO ---
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
        with st.form("login_v133"):
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
    # --- BARRA LATERAL (FIJA Y FUNCIONAL) ---
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        st.divider()
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, estado").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: {"id": row['id'], "estado": row.get('estado', 'ACTIVO')} for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON CALENDARIO) ---
    with tabs[0]:
        st.subheader("📅 Registro de Agenda")
        if mapa_cursos:
            m_a = st.selectbox("Seleccionar Materia:", ["---"] + list(mapa_cursos.keys()), key="ag_v133")
            if m_a != "---":
                with st.form("f_ag_v133"):
                    f_h = datetime.date.today()
                    st.write(f"Fecha de hoy: {f_h.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados hoy")
                    st.divider()
                    st.write("📌 Programar Tarea")
                    f_t = st.date_input("Fecha de entrega", value=f_h + datetime.timedelta(days=7))
                    desc_t = st.text_area("Descripción de la tarea")
                    if st.form_submit_button("💾 GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_a]["id"],
                            "fecha": str(f_h),
                            "contenido_clase": temas,
                            "tarea_proxima": desc_t,
                            "fecha_tarea": str(f_t)
                        }).execute()
                        st.success("✅ Guardado correctamente.")
                        st.rerun()
        else: st.info("Cree una materia en 'Cursos' primero.")

    # --- TAB 1: ALUMNOS (FILTROS + INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("f_ins_v133"):
                ni_n, ni_a = st.text_input("Nombre"), st.text_input("Apellido")
                ni_c = st.selectbox("Asignar a Curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
                if st.form_submit_button("💾 REGISTRAR"):
                    r_new = supabase.table("alumnos").insert({"nombre": ni_n, "apellido": ni_a, "estado": "ACTIVO"}).execute()
                    if r_new.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": r_new.data[0]['id'],
                            "profesor_id": u_data['id'],
                            "nombre_curso_materia": ni_c
                        }).execute()
                        st.rerun()

        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        f_m = fc1.selectbox("📍 Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="f_al_c_133")
        f_b = fc2.text_input("🔍 Apellido/Nombre:", key="f_al_b_133").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        try:
            r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_l.data:
                for it in r_l.data:
                    al = it['alumnos']
                    if (f_m == "Todas" or it['nombre_curso_materia'] == f_m) and (f_b in al['nombre'].lower() or f_b in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                            with st.form(f"ed_al_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3)
                                if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                                if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if b3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
            else: st.info("No hay alumnos.")
        except: st.error("Error al cargar alumnos.")

    # --- TAB 2: ASISTENCIA (FILTROS CRUZADOS) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="f_as_c_133")
            f_as_n = ac2.text_input("Buscar por Apellido:", key="f_as_n_133").lower()
            st.markdown('</div>', unsafe_allow_html=True)
            if f_as_c != "---":
                r_as = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_as_c).not_.is_("alumno_id", "null").execute()
                for it in r_as.data:
                    al = it['alumnos']
                    if f_as_n in al['apellido'].lower():
                        with st.expander(f"📌 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"f_as_{al['id']}"):
                                est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                if st.form_submit_button("💾 GUARDAR ASISTENCIA"):
                                    supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": f_as_c, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                    st.success("Guardado.")
        else: st.info("Cree un curso primero.")

    # --- TAB 4: CURSOS (ORDEN Y ESTADO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("n_c_v133"):
            n_mat = st.text_input("Nombre de la nueva Materia")
            if st.form_submit_button("➕ CREAR MATERIA"):
                # Se eliminó la etiqueta de estado para evitar errores de API en tablas restringidas
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_mat}).execute()
                st.rerun()
        st.divider()
        if mapa_cursos:
            for n, info in mapa_cursos.items():
                est_label = "st-active" if info["estado"] == "ACTIVO" else "st-inactive"
                with st.expander(f"📘 {n}"):
                    st.markdown(f'<span class="{est_label}">{info["estado"]}</span>', unsafe_allow_html=True)
                    with st.form(f"ed_c_{info['id']}"):
                        st.text_input("Materia", value=n)
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                        if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                        if b3.form_submit_button("🗑️ BORRAR DEFINITIVO"):
                            supabase.table("inscripciones").delete().eq("id", info['id']).execute()
                            st.rerun()
