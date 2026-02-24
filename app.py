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

# Inicialización de estados para evitar errores de renderizado
if 'user' not in st.session_state: st.session_state.user = None
if 'confirm_alu' not in st.session_state: st.session_state.confirm_alu = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; margin-bottom: 20px; }
    .empty-msg { padding: 30px; border-radius: 12px; background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.1); text-align: center; color: #777; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CORREGIDO PARA ENTER Y RED) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        # Formulario con validación previa para evitar el error de red al dar ENTER
        u_input = st.text_input("Sede", key="login_sede").strip().lower()
        p_input = st.text_input("Clave", type="password", key="login_pass")
        
        if st.button("Entrar", use_container_width=True):
            email_real = ""
            if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
            elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
            
            if email_real:
                try:
                    res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p_input).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Clave incorrecta.")
                except: st.error("Error de conexión. Intentá de nuevo.")
            else: st.error("Sede no válida.")

else:
    user = st.session_state.user
    hoy = datetime.date.today()
    st.sidebar.write(f"Sede: {'Cambridge' if 'cambridge' in user['email'] else 'Daguerre'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA DE CURSOS SEGURA ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 1: ALUMNOS (ARREGLADO) ---
    with tabs[1]:
        st.subheader("Inscripción de Estudiantes")
        if not df_cursos.empty:
            opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_sel = st.selectbox("Elegir Curso:", opciones, key="sel_alu_ins")
            
            with st.form("form_registro_alumno", clear_on_submit=True):
                nom = st.text_input("Nombre del Alumno")
                ape = st.text_input("Apellido del Alumno")
                if st.form_submit_button("Inscribir"):
                    if nom and ape:
                        st.session_state.confirm_alu = {"nom": nom, "ape": ape, "curso": c_sel}
            
            if st.session_state.confirm_alu:
                d = st.session_state.confirm_alu
                st.warning(f"¿Inscribir a {d['nom']} {d['ape']} en {d['curso']}?")
                if st.button("✅ SÍ, CONFIRMAR"):
                    try:
                        nuevo = supabase.table("alumnos").insert({"nombre": d['nom'], "apellido": d['ape']}).execute()
                        c_n, c_h = d['curso'].split(" | ")
                        supabase.table("inscripciones").insert({
                            "alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], 
                            "nombre_curso_materia": c_n, "horario": c_h, "anio_lectivo": 2026
                        }).execute()
                        st.session_state.confirm_alu = None
                        st.success("¡Alumno registrado!")
                        st.rerun()
                    except: st.error("Error al registrar.")
        else:
            st.markdown('<div class="empty-msg">👥 No podés inscribir alumnos porque no tenés Cursos creados.<br>Andá a la pestaña "Cursos" para empezar.</div>', unsafe_allow_html=True)

    # --- TAB 2: ASISTENCIA Y TAB 3: NOTAS (CON LEYENDAS) ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            st.markdown(f'<div class="empty-msg">🚫 No hay alumnos registrados.<br>Inscribí al menos un alumno en la pestaña "Alumnos" para activar esta sección.</div>', unsafe_allow_html=True)

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            st.info("Elegí una materia para cargar la clase de hoy.")
        else:
            st.markdown('<div class="empty-msg">📅 La agenda se activará cuando crees tu primer curso.</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_n, col_b = st.columns([4, 1])
                col_n.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
                if col_b.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            st.write("➕ Añadir Materia")
            nc = st.text_input("Nombre de la Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
