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
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<h1 style="text-align:center;">ClassTrack 360</h1>', unsafe_allow_html=True)
        with st.form("login_v86"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
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
    ahora = datetime.datetime.now()
    u_data = st.session_state.user
    
    with st.sidebar:
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- DATOS GLOBALES ---
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
            m_sel = st.selectbox("Elegir Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_age_v86")
            if m_sel != "--- Elegir ---":
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_new_bit", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados")
                        t2 = st.text_area("Tarea")
                        if st.form_submit_button("Guardar"):
                            supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_sel], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                            st.rerun()
                with c2:
                    st.write("### Historial")
                    r_h = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[m_sel]).order("fecha", desc=True).execute()
                    if r_h.data:
                        for entry in r_h.data:
                            with st.expander(f"📝 {entry['fecha']}"):
                                with st.form(f"ed_bit_{entry['id']}"):
                                    e_cont = st.text_area("Contenido", value=entry['contenido_clase'])
                                    e_tar = st.text_area("Tarea", value=entry['tarea_proxima'] if entry['tarea_proxima'] else "")
                                    b1, b2, b3 = st.columns(3)
                                    if b1.form_submit_button("ACTUALIZAR"):
                                        supabase.table("bitacora").update({"contenido_clase": e_cont, "tarea_proxima": e_tar}).eq("id", entry['id']).execute()
                                        st.rerun()
                                    if b2.form_submit_button("CANCELAR"): st.rerun()
                                    if b3.form_submit_button("ELIMINAR"):
                                        supabase.table("bitacora").delete().eq("id", entry['id']).execute()
                                        st.rerun()

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Alumnos")
        with st.expander("➕ Inscribir Alumno"):
            if not df_cursos.empty:
                with st.form("f_ins_v86", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Confirmar"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()

        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                    with st.form(f"ed_al_{alu['id']}"):
                        n_nom = st.text_input("Nombre", value=alu['nombre'])
                        n_ape = st.text_input("Apellido", value=alu['apellido'])
                        ba1, ba2 = st.columns(2)
                        if ba1.form_submit_button("ACTUALIZAR"):
                            supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape}).eq("id", alu['id']).execute()
                            st.rerun()
                        if ba2.form_submit_button("CANCELAR"): st.rerun()

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if not df_cursos.empty:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v86")
            sub_as = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_as[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    with st.form("f_as_v86"):
                        checks = []
                        for it in r_as.data:
                            al = it['alumnos']
                            est = st.radio(f"{al['apellido']}", ["Presente", "Ausente"], key=f"as_{al['id']}", horizontal=True)
                            checks.append({"id": al['id'], "est": est})
                        if st.form_submit_button("Guardar"):
                            for c in checks:
                                supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                            st.success("Guardado")
            with sub_as[1]:
                f_q = st.date_input("Fecha:", value=ahora.date())
                rv = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                if rv.data:
                    for r in rv.data: st.write(f"• {r['alumnos']['apellido']}: {r['estado']}")
                else: st.info("ℹ️ No hay registros para esta fecha.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        if not df_cursos.empty:
            m_nt = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_nt_v86")
            sub_nt = st.tabs(["📝 Cargar", "🔍 Consultar"])
            with sub_nt[0]:
                r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    with st.form("f_nt_v86"):
                        inst = st.selectbox("Instancia", ["Parcial 1", "Parcial 2", "TP", "Final"])
                        nl = []
                        for it
