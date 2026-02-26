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

# --- ESTILO CSS (ETIQUETAS VERDE/ROJO) ---
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
        with st.form("login_v98"):
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

    # --- CARGA CRÍTICA DE DATOS ---
    df_cursos = pd.DataFrame()
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            df_cursos = pd.DataFrame(r_c.data)
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (BLINDADA) ---
    with tabs[2]:
        st.subheader("Asistencia")
        if not df_cursos.empty:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v98")
            sub_as = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_as[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    with st.form("f_as_v98"):
                        checks = []
                        for it in r_as.data:
                            al = it['alumnos']
                            est = st.radio(f"{al['apellido']}", ["Presente", "Ausente"], key=f"as_v98_{al['id']}", horizontal=True)
                            checks.append({"id": al['id'], "est": est})
                        if st.form_submit_button("GUARDAR ASISTENCIA"):
                            for c in checks:
                                supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                            st.success("✅ Guardado")
                else: st.info("ℹ️ No hay alumnos inscriptos en esta materia.")
            with sub_as[1]:
                f_q = st.date_input("Fecha:", value=ahora.date())
                try:
                    rv = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                    if rv.data:
                        for r in rv.data: st.write(f"• {r['alumnos']['apellido']}: {r['estado']}")
                    else: st.info("ℹ️ No hay registros para esta fecha.")
                except: st.info("ℹ️ No hay datos disponibles.")
        else:
            st.info("ℹ️ No hay registros de asistencia disponibles porque no hay materias creadas.")

    # --- TAB 3: NOTAS (BLINDADA) ---
    with tabs[3]:
        st.subheader("Notas")
        st.info("ℹ️ No hay registros de notas disponibles para el alumno seleccionado.")

    # --- TAB 4: CURSOS (ORDEN INVERSO Y BORRADO DEFINITIVO) ---
    with tabs[4]:
        st.subheader("Gestión de Cursos")
        if not df_cursos.empty:
            st.write("### Mis Materias")
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"ed_c_v98_{r['id']}"):
                        n_mat = st.text_input("Nombre de la Materia", value=r['nombre_curso_materia'])
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.form_submit_button("GUARDAR CAMBIOS"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", r['id']).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
                        if bc3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                            st.session_state[f"del_c_{r['id']}"] = True
                    
                    if st.session_state.get(f"del_c_{r['id']}"):
                        st.error(f"### 🚨 ¿BORRAR MATERIA {r['nombre_curso_materia']}? \n Se eliminará el curso y sus registros.")
                        c_col1, c_col2 = st.columns(2)
                        if c_col1.button("SÍ, BORRAR", key=f"yc_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
                        if c_col2.button("NO", key=f"nc_{r['id']}"):
                            del st.session_state[f"del_c_{r['id']}"]
                            st.rerun()
        else:
            st.info("ℹ️ No tiene materias creadas actualmente.")

        st.divider()
        with st.form("f_new_c_v98"):
            st.write("### ➕ Crear Nueva Materia")
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVO CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
