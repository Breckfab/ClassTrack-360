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
    .login-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_v81"):
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

    # Carga de Materias
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON BOTÓN CANCELAR) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: st.info("Crea un curso primero.")
        else:
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
            m_sel = st.selectbox("--- Elegir Curso o Materia ---", ["--- Elegir Curso o Materia ---"] + list(mapa_cursos.keys()), key="sb_age_v81")
            
            if m_sel != "--- Elegir Curso o Materia ---":
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_new_bit", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados")
                        t2 = st.text_area("Tarea próxima")
                        if st.form_submit_button("Guardar"):
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
                                    
                                    # BOTONES ALINEADOS
                                    col_upd, col_can, col_del = st.columns(3)
                                    if col_upd.form_submit_button("ACTUALIZAR"):
                                        supabase.table("bitacora").update({"contenido_clase": e_cont, "tarea_proxima": e_tar}).eq("id", entry['id']).execute()
                                        st.success("Cambiado")
                                        st.rerun()
                                    if col_can.form_submit_button("CANCELAR"):
                                        st.rerun()
                                    if col_del.form_submit_button("ELIMINAR"):
                                        supabase.table("bitacora").delete().eq("id", entry['id']).execute()
                                        st.rerun()
                    else: st.info("ℹ️ Sin historial.")

    # --- TAB 1: ALUMNOS (CON BOTÓN CANCELAR) ---
    with tabs[1]:
        st.subheader("Alumnos")
        r_insc = supabase.table("inscripciones").select("id, alumno_id, nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_insc.data:
            for item in r_insc.data:
                r_alu = supabase.table("alumnos").select("*").eq("id", item['alumno_id']).execute()
                if r_alu.data:
                    alu = r_alu.data[0]
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({item['nombre_curso_materia']})"):
                        with st.form(f"ed_alu_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            b_a1, b_a2 = st.columns(2)
                            if b_a1.form_submit_button("ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape}).eq("id", alu['id']).execute()
                                st.rerun()
                            if b_a2.form_submit_button("CANCELAR"):
                                st.rerun()
