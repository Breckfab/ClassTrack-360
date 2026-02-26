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
    
    /* LOGO PROFESIONAL CSS */
    .logo-container { text-align: center; padding: 20px; }
    .logo-text { 
        font-size: 3.5rem; font-weight: 800; 
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -2px; margin-bottom: 0px;
    }
    .logo-sub { color: #888; font-size: 1rem; letter-spacing: 5px; text-transform: uppercase; margin-top: -10px; }
    
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 8px; border-radius: 4px; background: rgba(255,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        # LOGO PROFESIONAL NO ROTO
        st.markdown("""
            <div class="logo-container">
                <div class="logo-text">CT360</div>
                <div class="logo-sub">ClassTrack</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_v92"):
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
        st.markdown('<div style="font-size:1.5rem; font-weight:800; color:#4facfe;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- DATOS GLOBALES ---
    df_cursos = pd.DataFrame()
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            df_cursos = pd.DataFrame(r_c.data)
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
    except: pass

    # --- TAB 1: ALUMNOS (BORRAR, EDITAR, GUARDAR, ACTIVO/INACTIVO) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v92", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()

        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    st_label = alu.get('estado', 'ACTIVO')
                    st_class = "status-active" if st_label == "ACTIVO" else "status-inactive"
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                        st.markdown(f"Estado: <span class='{st_class}'>{st_label}</span>", unsafe_allow_html=True)
                        with st.form(f"ed_al_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            n_est = st.radio("Cambiar Estado", ["ACTIVO", "INACTIVO"], index=0 if st_label == "ACTIVO" else 1, horizontal=True)
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape, "estado": n_est}).eq("id", alu['id']).execute()
                                st.rerun()
                            if c2.form_submit_button("CANCELAR"): st.rerun()
                            if c3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                                st.session_state[f"confirm_{alu['id']}"] = True
                        
                        if st.session_state.get(f"confirm_{alu['id']}"):
                            st.error(f"### 🚨 ADVERTENCIA: BORRADO DEFINITIVO \n ¿Está seguro de eliminar a **{alu['nombre']} {alu['apellido']}**? Esta acción no se puede deshacer.")
                            b1, b2 = st.columns(2)
                            if b1.button("SÍ, ELIMINAR AHORA", key=f"y_{alu['id']}"):
                                supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                st.rerun()
                            if b2.button("NO, MANTENER REGISTRO", key=f"n_{alu['id']}"):
                                del st.session_state[f"confirm_{alu['id']}"]
                                st.rerun()
        else: st.info("ℹ️ No hay alumnos registrados.")

    # --- LAS DEMÁS PESTAÑAS (AGENDA, ASISTENCIA, NOTAS, CURSOS) ---
    # Se mantienen con la lógica de botones y leyendas obligatorias
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            m_sel = st.selectbox("Elegir Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_age_v92")
            if m_sel != "--- Elegir ---":
                with st.form("f_bit"):
                    t1 = st.text_area("Contenido de la clase")
                    t2 = st.text_area("Tarea próxima")
                    if st.form_submit_button("GUARDAR CLASE"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_sel], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                        st.rerun()
        else: st.info("ℹ️ No hay registros de clase disponibles porque no hay cursos creados.")

    with tabs[3]:
        st.subheader("Notas")
        st.info("ℹ️ No hay registros de notas disponibles para el alumno seleccionado.")

    with tabs[4]:
        st.subheader("Configuración de Cursos")
        with st.form("f_new_cur"):
            nc = st.text_input("Nombre de la materia")
            if st.form_submit_button("GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
