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
        with st.form("login_v95"):
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

    # --- CARGA PREVIA DE DATOS (ESTABILIDAD TOTAL) ---
    df_cursos = pd.DataFrame()
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            df_cursos = pd.DataFrame(r_c.data)
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (BOTONES OBLIGATORIOS Y ETIQUETAS) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v95", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else: st.warning("Debe crear una materia primero en la pestaña 'Cursos'.")

        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    st_label = alu.get('estado', 'ACTIVO')
                    st_class = "status-active" if st_label == "ACTIVO" else "status-inactive"
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                        st.markdown(f"Estado: <span class='{st_class}'>{st_label}</span>", unsafe_allow_html=True)
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
                            st.error(f"### 🚨 ¿ESTÁ SEGURO? \n Se borrará permanentemente a **{alu['nombre']} {alu['apellido']}**.")
                            b1, b2 = st.columns(2)
                            if b1.button("SÍ, BORRAR", key=f"y_{alu['id']}"):
                                supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                st.rerun()
                            if b2.button("NO", key=f"n_{alu['id']}"):
                                del st.session_state[f"del_{alu['id']}"]
                                st.rerun()
        else: st.info("ℹ️ No hay alumnos inscriptos.")

    # --- TAB 2: ASISTENCIA (CORRECCIÓN DE ERROR API) ---
    with tabs[2]:
        st.subheader("Asistencia")
        if not df_cursos.empty:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v95")
            sub_as = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_as[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    with st.form("f_as_v95"):
                        checks = []
                        for it in r_as.data:
                            al = it['alumnos']
                            est = st.radio(f"{al['apellido']}", ["Presente", "Ausente"], key=f"as_v95_{al['id']}", horizontal=True)
                            checks.append({"id": al['id'], "est": est})
                        if st.form_submit_button("GUARDAR ASISTENCIA"):
                            for c in checks:
                                supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                            st.success("✅ Guardado")
            with sub_as[1]:
                f_q = st.date_input("Fecha:", value=ahora.date())
                # Blindaje: solo consulta si hay datos seleccionados
                if m_as and f_q:
                    try:
                        rv = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                        if rv.data:
                            for r in rv.data: st.write(f"• {r['alumnos']['apellido']}: {r['estado']}")
                        else: st.info("ℹ️ No hay registros para esta fecha.")
                    except: st.info("ℹ️ No hay registros disponibles.")
        else: st.info("ℹ️ No hay materias para gestionar asistencia.")

    # --- TAB 3: NOTAS (LEYENDA OBLIGATORIA) ---
    with tabs[3]:
        st.subheader("Notas")
        st.info("ℹ️ No hay registros de notas disponibles para el alumno seleccionado.")

    # --- TAB 4: CURSOS (GUARDAR, EDITAR, BORRAR) ---
    with tabs[4]:
        st.subheader("Cursos")
        with st.form("f_new_c_v95"):
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVO CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"ed_c_v95_{r['id']}"):
                        n_mat = st.text_input("Nombre", value=r['nombre_curso_materia'])
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.form_submit_button("ACTUALIZAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", r['id']).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
                        if bc3.form_submit_button("BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
