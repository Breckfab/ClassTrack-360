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

# --- ESTILO CSS (ETIQUETAS VERDE/ROJO Y LOGO) ---
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
        with st.form("login_v99"):
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

    # --- CARGA CRÍTICA (MATERIAS) ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA Y CON BUSCADOR) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        sub_age = st.tabs(["➕ Nueva Clase", "🔍 Historial y Tareas"])
        with sub_age[0]:
            if mapa_cursos:
                m_sel = st.selectbox("Elegir Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v99")
                if m_sel != "--- Seleccionar ---":
                    with st.form("f_age_v99"):
                        t1 = st.text_area("Temas dictados")
                        t2 = st.text_area("Tarea próxima")
                        if st.form_submit_button("GUARDAR CLASE"):
                            supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_sel], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                            st.rerun()
            else: st.info("ℹ️ Para registrar una clase, primero cree una materia en la pestaña 'Cursos'.")
        
        with sub_age[1]:
            st.write("### 🔍 Buscador de Clases Pasadas")
            m_bus = st.selectbox("Filtrar por Materia:", ["--- Todas ---"] + list(mapa_cursos.keys()), key="sb_bus_v99")
            try:
                q_h = supabase.table("bitacora").select("*, inscripciones(nombre_curso_materia)")
                if m_bus != "--- Todas ---": q_h = q_h.eq("inscripcion_id", mapa_cursos[m_bus])
                res_h = q_h.order("fecha", desc=True).execute()
                if res_h.data:
                    for e in res_h.data:
                        with st.expander(f"📅 {e['fecha']} - {e['inscripciones']['nombre_curso_materia']}"):
                            st.write(f"**Temas:** {e['contenido_clase']}")
                            st.write(f"**Tarea:** {e['tarea_proxima']}")
                else: st.info("ℹ️ No hay clases registradas aún.")
            except: st.info("ℹ️ Error al cargar historial.")

    # --- TAB 1: ALUMNOS (RECUPERADA: LISTA Y BUSCADOR) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        # 1. LISTADO Y BUSCADOR
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                bus_alu = st.text_input("🔍 Buscar alumno por nombre o apellido").lower()
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu and (bus_alu in alu['nombre'].lower() or bus_alu in alu['apellido'].lower()):
                        st_label = alu.get('estado', 'ACTIVO')
                        st_class = "status-active" if st_label == "ACTIVO" else "status-inactive"
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                            st.markdown(f"Estado: <span class='{st_class}'>{st_label}</span>", unsafe_allow_html=True)
                            with st.form(f"ed_al_v99_{alu['id']}"):
                                n_nom = st.text_input("Nombre", value=alu['nombre'])
                                n_ape = st.text_input("Apellido", value=alu['apellido'])
                                n_est = st.radio("Estado", ["ACTIVO", "INACTIVO"], index=0 if st_label == "ACTIVO" else 1, horizontal=True)
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("ACTUALIZAR"):
                                    supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape, "estado": n_est}).eq("id", alu['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("CANCELAR"): st.rerun()
                                if c3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                                    st.session_state[f"da_{alu['id']}"] = True
                            
                            if st.session_state.get(f"da_{alu['id']}"):
                                st.error(f"### 🚨 ¿BORRAR A {alu['nombre']}? Acción irreversible.")
                                if st.button("SÍ, BORRAR DEFINITIVAMENTE", key=f"ya_{alu['id']}"):
                                    supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos actualmente.")
        except: st.info("ℹ️ Error al cargar la lista de alumnos.")

        st.divider()
        # 2. SIEMPRE MOSTRAR INSCRIPCIÓN (EVITA EL "EN NEGRO")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v99"):
                    m_ins = st.selectbox("Materia destino:", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else: st.warning("⚠️ Primero cree una materia en 'Cursos'.")

    # --- PESTAÑAS RESTANTES (BLINDADAS) ---
    with tabs[2]:
        st.subheader("Asistencia")
        st.info("ℹ️ No hay registros de asistencia disponibles.")
    with tabs[3]:
        st.subheader("Notas")
        st.info("ℹ️ No hay registros de notas disponibles.")
    with tabs[4]:
        st.subheader("Gestión de Cursos")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    if st.button(f"BORRAR CURSO {n}", key=f"bc_{i}"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
        st.divider()
        with st.form("f_c_v99"):
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
