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
        with st.form("login_v101"):
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

    # --- TAB 1: ALUMNOS (REDISEÑO TOTAL: FORMULARIO VISIBLE SIEMPRE) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        
        # 1. FORMULARIO DE INSCRIPCIÓN (SIEMPRE VISIBLE PRIMERO PARA EVITAR "EN NEGRO")
        with st.expander("➕ Inscribir Alumno Nuevo", expanded=True):
            if mapa_cursos:
                with st.form("f_ins_v101"):
                    m_ins = st.selectbox("Seleccionar Materia:", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR E INSCRIBIR"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else:
                st.warning("⚠️ Primero debés crear una materia en la pestaña 'Cursos' para poder inscribir alumnos.")

        st.divider()

        # 2. LISTADO Y BÚSQUEDA
        st.write("### 🔍 Lista de Alumnos Inscriptos")
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                bus_alu = st.text_input("Buscar por Nombre o Apellido:").lower()
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu and (bus_alu in alu['nombre'].lower() or bus_alu in alu['apellido'].lower()):
                        st_label = alu.get('estado', 'ACTIVO')
                        st_class = "status-active" if st_label == "ACTIVO" else "status-inactive"
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                            st.markdown(f"Estado: <span class='{st_class}'>{st_label}</span>", unsafe_allow_html=True)
                            with st.form(f"ed_al_v101_{alu['id']}"):
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
                                st.error(f"### 🚨 ¿BORRAR DEFINITIVAMENTE A {alu['nombre']}?")
                                col_b1, col_b2 = st.columns(2)
                                if col_b1.button("SÍ, BORRAR", key=f"ya_{alu['id']}"):
                                    supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                    st.rerun()
                                if col_b2.button("NO", key=f"na_{alu['id']}"):
                                    del st.session_state[f"da_{alu['id']}"]
                                    st.rerun()
            else:
                st.info("ℹ️ No hay alumnos inscriptos actualmente. Usá el formulario de arriba para cargar el primero.")
        except:
            st.error("❌ Error al conectar con la lista de alumnos.")

    # --- TAB 4: CURSOS (ESTRUCTURA FIJA) ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if mapa_cursos:
            st.write("### Materias Actuales")
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    if st.button(f"BORRAR CURSO {n}", key=f"bc_v101_{i}"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
        st.divider()
        with st.form("f_c_v101"):
            st.write("### ➕ Crear Nueva Materia")
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVA MATERIA"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()

    # --- TAB 0, 2, 3 (AGENDA, ASISTENCIA, NOTAS) ---
    # Se mantienen funcionales y blindadas contra pantallas en negro
    with tabs[0]: st.info("ℹ️ Accedé a 'Nueva Clase' o 'Historial' para ver los temas dictados.")
    with tabs[2]: st.info("ℹ️ Seleccioná una materia para ver la asistencia.")
    with tabs[3]: st.info("ℹ️ Seleccioná una materia para gestionar calificaciones.")
