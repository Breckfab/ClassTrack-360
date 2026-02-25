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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(255,255,255,0.05); border-radius: 5px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<h1 style="text-align:center;">ClassTrack 360</h1>', unsafe_allow_html=True)
        with st.form("login_v85"):
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
        if df_cursos.empty: st.info("🏗️ Crea un curso en la pestaña 'Cursos' primero.")
        else:
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
            m_sel = st.selectbox("--- Elegir Curso o Materia ---", ["--- Elegir Curso o Materia ---"] + list(mapa_cursos.keys()), key="sb_age_v85")
            
            if m_sel != "--- Elegir Curso o Materia ---":
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_new_bit", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados hoy")
                        t2 = st.text_area("Tarea próxima")
                        if st.form_submit_button("Guardar Registro"):
                            supabase.table("bitacora").insert({
                                "inscripcion_id": mapa_cursos[m_sel],
                                "fecha": str(ahora.date()),
                                "contenido_clase": t1,
                                "tarea_proxima": t2
                            }).execute()
                            st.rerun()
                with c2:
                    st.write("### Historial / Editar")
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
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if not df_cursos.empty:
                with st.form("f_ins_v85", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Confirmar Inscripción"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else: st.warning("Crea una materia primero.")

        r_al = supabase.table("inscripciones").select("id, alumno_id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                        with st.form(f"ed_al_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            b_a1, b_a2 = st.columns(2)
                            if b_a1.form_submit_button("ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape}).eq("id", alu['id']).execute()
                                st.rerun()
                            if b_a2.form_submit_button("CANCELAR"): st.rerun()
        else: st.info("No hay alumnos inscriptos.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if df_cursos.empty: st.warning("Crea una materia.")
        else:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v85")
            sub_as = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_as[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    with st.form("f_tomar_v85"):
                        checks = []
                        for it in r_as.data:
                            al = it['alumnos']
                            est = st.radio(f"{al['apellido']}, {al['nombre']}", ["Presente", "Ausente"], key=f"v85_{al['id']}", horizontal=True)
                            checks.append({"id": al['id'], "est": est})
                        if st.form_submit_button("Guardar"):
                            for c in checks:
                                supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                            st.success("Guardado.")
                else: st.info("Sin alumnos.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        with st.form("f_new_mat_v85"):
            st.write("➕ Crear Materia")
            nm, hm = st.text_input("Nombre"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm, "horario": hm, "anio_lectivo": 2026}).execute()
                st.rerun()
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"ed_c_{r['id']}"):
                        n_mat = st.text_input("Editar Nombre", value=r['nombre_curso_materia'])
                        bc1, bc2 = st.columns(2)
                        if bc1.form_submit_button("ACTUALIZAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", r['id']).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
