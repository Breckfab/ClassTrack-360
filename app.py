import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v179", layout="wide")

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
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v179"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com"
                try:
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado.")
                except: st.error("Error de conexión.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👨‍🏫 {u_data['nombre']}")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB ASISTENCIA ---
    with tabs[2]:
        st.subheader("✅ Asistencia Colectiva")
        c1, c2 = st.columns(2)
        sel_as = c1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v179")
        f_as = c2.date_input("Fecha:", datetime.date.today())
        if sel_as != "---":
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
            for it in r_as.data:
                al = it['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    with st.form(f"as_{al['id']}_{f_as}"):
                        est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                        if st.form_submit_button("💾 GUARDAR"):
                            supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_as, "estado": est, "fecha": str(f_as)}).execute()
                            st.success("Ok")

    # --- TAB NOTAS (CORREGIDA LÍNEA 150) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Calificaciones")
        sel_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v179")
        if sel_nt != "---":
            r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
            for it in r_nt.data:
                al = it['alumnos']
                # FIX LÍNEA 150: Cálculo seguro de promedio
                res_n = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                prom = 0.0
                if res_n.data:
                    vals = [float(n['calificacion']) for n in res_n.data]
                    prom = sum(vals) / len(vals)
                
                with st.container():
                    st.markdown(f'<div class="planilla-row">📝 {al["apellido"].upper()}, {al["nombre"]} <span style="float:right;">Promedio: <span class="promedio-badge">{prom:.2f}</span></span></div>', unsafe_allow_html=True)
                    with st.form(f"nt_{al['id']}"):
                        n_v = st.number_input("Nota:", 1.0, 10.0, value=None, placeholder="7.00")
                        if st.form_submit_button("💾 GRABAR NOTA"):
                            if n_v:
                                supabase.table("notas").insert({"alumno_id": str(al['id']), "profesor_id": u_data['id'], "materia": sel_nt, "calificacion": float(n_v)}).execute()
                                st.success("Nota grabada"); time.sleep(0.5); st.rerun()

    # --- TAB CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("new_cur"):
            c_nom = st.text_input("Materia")
            if st.form_submit_button("💾 CREAR"):
                if c_nom:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": c_nom, "anio_lectivo": 2026}).execute()
                    st.rerun()
