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
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; text-align: center; margin-bottom: 20px; }
    .confirm-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 10px; background-color: rgba(255, 75, 75, 0.1); margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                try:
                    res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado.")
                except: st.error("Error de conexión con la base de datos.")

else:
    user = st.session_state.user
    st.sidebar.write(f"Conectado: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CONSULTA DE CURSOS (PROTEGIDA) ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            df_cursos = pd.DataFrame(res_c.data)
    except:
        st.sidebar.error("Error al cargar cursos.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if not df_cursos.empty:
            with st.form("form_ins_alu", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                c_sel = st.selectbox("Asignar a Curso", opciones)
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                if st.form_submit_button("Inscribir"):
                    if nom_a and ape_a:
                        st.session_state.confirm_alu = {"nom": nom_a, "ape": ape_a, "curso": c_sel}
            
            if st.session_state.get('confirm_alu'):
                d = st.session_state.confirm_alu
                st.warning(f"¿Inscribir a {d['nom']} {d['ape']}?")
                if st.button("✅ SÍ, CONFIRMAR"):
                    try:
                        nuevo = supabase.table("alumnos").insert({"nombre": d['nom'], "apellido": d['ape']}).execute()
                        c_n, c_h = d['curso'].split(" | ")
                        supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_n, "horario": c_h, "anio_lectivo": 2026}).execute()
                        del st.session_state.confirm_alu
                        st.success("Alumno inscrito.")
                        st.rerun()
                    except: st.error("Error al guardar alumno.")
        else: st.info("Cargá un curso primero en la pestaña 'Cursos'.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col_c2.button("Borrar", key=f"del_cur_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_c"):
            nc = st.text_input("Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Añadir Curso"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                st.rerun()

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Bitácora Diaria")
        if not df_cursos.empty:
            opciones_a = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia de hoy", opciones_a)
            with st.form("form_agenda"):
                temas = st.text_area("Temas")
                if st.form_submit_button("Guardar Clase"):
                    st.success("Clase registrada.")
        else: st.info("Sin cursos cargados.")
