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
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .empty-msg { padding: 20px; border-radius: 10px; background: rgba(255, 255, 255, 0.05); border: 1px dashed rgba(255, 255, 255, 0.2); text-align: center; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CORREGIDO PARA ENTER) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        # Usamos un formulario para capturar el ENTER correctamente
        with st.form("login_form"):
            u_input = st.text_input("Sede").strip().lower()
            p = st.text_input("Clave", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                email_real = ""
                if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
                
                if email_real != "":
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de red. Verificá la conexión.")
                else: st.error("Sede no válida.")

else:
    user = st.session_state.user
    hoy = datetime.date.today()
    st.sidebar.write(f"Sede activa")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Consulta de materias
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON RECORDATORIOS) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            opciones_a = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia de hoy", opciones_a)
            c_id = df_cursos[df_cursos['nombre_curso_materia'] == c_agenda.split(" | ")[0]].iloc[0]['id']
            
            # BUSCAR RECORDATORIO DE TAREA
            try:
                # Buscamos en la bitácora si hay tareas que venzan HOY para este curso
                res_t = supabase.table("bitacora").select("tarea_descripcion").eq("curso_id", c_id).eq("tarea_vencimiento", str(hoy)).execute()
                if res_t.data:
                    st.markdown('<div class="reminder-box">🔔 <b>RECORDATORIO:</b> Tarea para revisar hoy:<br>' + 
                                f"{res_t.data[0]['tarea_descripcion']}</div>", unsafe_allow_html=True)
                else:
                    st.info("No hay tareas programadas para revisar hoy.")
            except: pass

            with st.form("registro_hoy"):
                temas = st.text_area("Contenidos dictados hoy:")
                tarea_nueva = st.text_area("Tarea para la próxima clase:")
                fecha_venc = st.date_input("¿Para qué día es la tarea?", hoy + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    if temas:
                        supabase.table("bitacora").insert({
                            "curso_id": int(c_id), "profesor_id": user['id'], "fecha": str(hoy),
                            "temas": temas, "tarea_descripcion": tarea_nueva, "tarea_vencimiento": str(fecha_venc),
                            "docente_nombre": user['email']
                        }).execute()
                        st.success("✅ Guardado en bitácora.")
                    else: st.warning("Completá los temas dictados.")
        else:
            st.markdown('<div class="empty-msg">Primero creá una materia en la pestaña "Cursos".</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS (PARA LIMPIAR LOS REPETIDOS DE LA IMAGEN 06) ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col2.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_c"):
            st.write("➕ Añadir Materia")
            nc = st.text_input("Nombre")
            hc = st.text_input("Horario")
            if st.form_submit_button("Añadir"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
