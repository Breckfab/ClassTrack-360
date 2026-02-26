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

# --- ESTILO CSS PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 8px; border-radius: 4px; background: rgba(255,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v104"):
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
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE DATOS MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Tareas")
        if mapa_cursos:
            sub_age = st.tabs(["➕ Nueva Clase", "🔍 Historial"])
            with sub_age[0]:
                m_age = st.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v104")
                if m_age != "--- Seleccionar ---":
                    with st.form("f_age_v104"):
                        t1 = st.text_area("Contenido dictado hoy")
                        t2 = st.text_area("Tarea para la próxima")
                        if st.form_submit_button("GUARDAR CLASE"):
                            supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_age], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                            st.rerun()
            with sub_age[1]:
                st.write("### 🔍 Consultar clases pasadas")
                res_h = supabase.table("bitacora").select("*, inscripciones(nombre_curso_materia)").order("fecha", desc=True).execute()
                if res_h.data:
                    for e in res_h.data:
                        with st.expander(f"📅 {e['fecha']} - {e['inscripciones']['nombre_curso_materia']}"):
                            st.write(f"**Temas:** {e['contenido_clase']}")
                            st.write(f"**Tarea:** {e['tarea_proxima']}")
        else: st.info("ℹ️ Cree una materia en 'Cursos' para empezar.")

    # --- TAB 1: ALUMNOS (RESTABLECIDA) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo", expanded=True):
            if mapa_cursos:
                with st.form("f_ins_v104"):
                    m_ins = st.selectbox("Materia:", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else: st.warning("⚠️ Sin materias creadas.")
        
        st.divider()
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                bus = st.text_input("🔍 Buscar Alumno:").lower()
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu and (bus in alu['nombre'].lower() or bus in alu['apellido'].lower()):
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']}"):
                            with st.form(f"ed_al_{alu['id']}"):
                                n_n = st.text_input("Nombre", value=alu['nombre'])
                                n_a = st.text_input("Apellido", value=alu['apellido'])
                                n_e = st.radio("Estado", ["ACTIVO", "INACTIVO"], index=0 if alu['estado']=="ACTIVO" else 1)
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("GUARDAR"):
                                    supabase.table("alumnos").update({"nombre": n_n, "apellido": n_a, "estado": n_e}).eq("id", alu['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("CANCELAR"): st.rerun()
                                if c3.form_submit_button("⚠️ BORRAR"):
                                    supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: pass

    # --- TAB 2: ASISTENCIA (RESTABLECIDA) ---
    with tabs[2]:
        st.subheader("Asistencia")
        if mapa_cursos:
            m_as = st.selectbox("Curso:", list(mapa_cursos.keys()), key="sb_as_v104")
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
            if r_as.data:
                with st.form("f_as_v104"):
                    for it in r_as.data:
                        al = it['alumnos']
                        st.radio(f"{al['apellido']}, {al['nombre']}", ["Presente", "Ausente"], key=f"as_v104_{al['id']}", horizontal=True)
                    if st.form_submit_button("GUARDAR ASISTENCIA"):
                        st.success("✅ Guardado")
            else: st.info("ℹ️ No hay alumnos para esta materia.")
        else: st.info("ℹ️ Sin materias.")

    # --- TAB 3: NOTAS (RESTABLECIDA) ---
    with tabs[3]:
        st.subheader("Notas")
        if mapa_cursos:
            m_nt = st.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_nt_v104")
            if m_nt != "--- Seleccionar ---":
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if r_al_n.data:
                    for item in r_al_n.data:
                        al = item['alumnos']
                        with st.expander(f"📝 {al['apellido']}, {al['nombre']}"):
                            with st.form(f"f_nt_{al['id']}"):
                                val = st.text_input("Nota")
                                des = st.text_input("Instancia")
                                if st.form_submit_button("GUARDAR NOTA"):
                                    supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": m_nt, "nota": val, "descripcion": des, "fecha": str(ahora.date())}).execute()
                                    st.rerun()
        else: st.info("ℹ️ Sin materias.")

    # --- TAB 4: CURSOS (CON TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_c_{i}"):
                        n_mat = st.text_input("Nombre", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", i).execute()
                            st.rerun()
                        if c2.form_submit_button("CANCELAR"): st.rerun()
                        if c3.form_submit_button("⚠️ BORRAR"):
                            st.error(f"¿Borrar {n}?")
                            if st.button("CONFIRMAR BORRADO", key=f"y_c_{i}"):
                                supabase.table("inscripciones").delete().eq("id", i).execute()
                                st.rerun()
        st.divider()
        with st.form("f_new_c_v104"):
            nc = st.text_input("Nueva Materia")
            if st.form_submit_button("GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
