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

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 5px; border-radius: 4px; }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 5px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        # CORRECCIÓN DE LOGO: Uso de título estilizado si la imagen falla
        st.markdown('<h1 style="text-align:center; color:#4facfe; font-size: 3rem;">🌀</h1>', unsafe_allow_html=True)
        st.markdown('<h1 style="text-align:center; margin-top:-20px;">ClassTrack 360</h1>', unsafe_allow_html=True)
        with st.form("login_v91"):
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
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<h2 style="color:#4facfe;">🌀 CT360</h2>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR DEL SISTEMA"):
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

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v91", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()

        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    st_label = "ACTIVO" if alu.get('estado') == "ACTIVO" else "INACTIVO"
                    st_style = "status-active" if st_label == "ACTIVO" else "status-inactive"
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({st_label})"):
                        with st.form(f"ed_al_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            n_est = st.radio("Estado", ["ACTIVO", "INACTIVO"], index=0 if st_label == "ACTIVO" else 1, horizontal=True)
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape, "estado": n_est}).eq("id", alu['id']).execute()
                                st.rerun()
                            if c2.form_submit_button("CANCELAR"): st.rerun()
                            if c3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                                st.session_state[f"del_{alu['id']}"] = True
                        
                        if st.session_state.get(f"del_{alu['id']}"):
                            st.error(f"### 🚨 ¿ESTÁ SEGURO? \n\n Se borrará a **{alu['nombre']} {alu['apellido']}** permanentemente.")
                            b1, b2 = st.columns(2)
                            if b1.button("SÍ, BORRAR", key=f"y_{alu['id']}"):
                                supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                st.rerun()
                            if b2.button("NO", key=f"n_{alu['id']}"):
                                del st.session_state[f"del_{alu['id']}"]
                                st.rerun()
        else: st.info("ℹ️ No hay registros de alumnos.")

    # --- TAB 2: ASISTENCIA (CORRECCIÓN ERROR LÍNEA 167) ---
    with tabs[2]:
        st.subheader("Asistencia")
        if not df_cursos.empty:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v91")
            sub_as = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_as[1]:
                f_q = st.date_input("Fecha:", value=ahora.date())
                # Validación para evitar el error de la captura: solo consulta si hay materia seleccionada
                if m_as:
                    try:
                        rv = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                        if rv.data:
                            for r in rv.data: st.write(f"• {r['alumnos']['apellido']}: {r['estado']}")
                        else: st.info("ℹ️ No hay registros para esta fecha.")
                    except: st.info("ℹ️ Error de conexión al consultar asistencia.")
        else: st.info("ℹ️ No hay materias para gestionar asistencia.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        st.info("ℹ️ No hay registros de notas disponibles para el alumno seleccionado.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Cursos")
        with st.form("f_new_c"):
            nm = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm, "anio_lectivo": 2026}).execute()
                st.rerun()
