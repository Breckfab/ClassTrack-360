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
        # LOGO #8 SELECCIONADO
        st.image("http://googleusercontent.com/image_collection/image_retrieval/17828270365318714682_3", width=200)
        st.markdown('<h1 style="text-align:center; margin-top:-30px;">ClassTrack 360</h1>', unsafe_allow_html=True)
        with st.form("login_v90"):
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
        st.image("http://googleusercontent.com/image_collection/image_retrieval/17828270365318714682_3", width=100)
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

    # --- TAB 1: ALUMNOS (BORRAR, EDITAR, GUARDAR, ACTIVO/INACTIVO) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v90", clear_on_submit=True):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()
            else: st.warning("Crea una materia primero.")

        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    status_class = "status-active" if alu.get('estado') == "ACTIVO" else "status-inactive"
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                        st.markdown(f"Estado actual: <span class='{status_class}'>{alu.get('estado', 'ACTIVO')}</span>", unsafe_allow_html=True)
                        with st.form(f"ed_al_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            n_est = st.radio("Estado", ["ACTIVO", "INACTIVO"], index=0 if alu.get('estado') == "ACTIVO" else 1, horizontal=True)
                            
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("EDITAR / ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape, "estado": n_est}).eq("id", alu['id']).execute()
                                st.rerun()
                            if c2.form_submit_button("CANCELAR"): st.rerun()
                            
                            # CUADRO ROJO DE ADVERTENCIA PARA BORRAR
                            if c3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                                st.session_state[f"confirm_del_{alu['id']}"] = True
                        
                        if st.session_state.get(f"confirm_del_{alu['id']}"):
                            st.error(f"### 🚨 ¿ESTÁ SEGURO? \n\n Se borrará a **{alu['nombre']} {alu['apellido']}** y todo su historial de notas y asistencia.")
                            col_b1, col_b2 = st.columns(2)
                            if col_b1.button("SÍ, BORRAR TODO", key=f"yes_{alu['id']}"):
                                supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                del st.session_state[f"confirm_del_{alu['id']}"]
                                st.rerun()
                            if col_b2.button("NO, CANCELAR", key=f"no_{alu['id']}"):
                                del st.session_state[f"confirm_del_{alu['id']}"]
                                st.rerun()
        else: st.info("ℹ️ No hay registros de alumnos disponibles.")

    # --- TAB 0: AGENDA (RESTO DE SECCIONES SIGUEN IGUAL PERO INTEGRADAS) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            m_sel = st.selectbox("Elegir Curso:", ["--- Elegir ---"] + list(mapa_cursos.keys()), key="sb_age_v90")
            if m_sel != "--- Elegir ---":
                with st.form("f_new_bit"):
                    t1 = st.text_area("Temas dictados")
                    t2 = st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR REGISTRO"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_sel], "fecha": str(ahora.date()), "contenido_clase": t1, "tarea_proxima": t2}).execute()
                        st.rerun()
                
                st.divider()
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
                                if b3.form_submit_button("BORRAR"):
                                    supabase.table("bitacora").delete().eq("id", entry['id']).execute()
                                    st.rerun()
                else: st.info("ℹ️ No hay registros de clase disponibles para este curso.")
        else: st.info("ℹ️ No hay registros de clases disponibles porque no hay cursos creados.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas de Alumnos")
        if not df_cursos.empty:
            st.info("ℹ️ No hay registros de notas disponibles para el alumno seleccionado.")
        else:
            st.info("ℹ️ No hay registros de notas disponibles porque no hay alumnos ni materias.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Cursos / Materias")
        with st.form("f_new_c"):
            nm = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVO CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm, "anio_lectivo": 2026}).execute()
                st.rerun()
        
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"ed_c_{r['id']}"):
                        n_mat = st.text_input("Nombre", value=r['nombre_curso_materia'])
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.form_submit_button("ACTUALIZAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", r['id']).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
                        if bc3.form_submit_button("BORRAR MATERIA"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
