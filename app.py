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

# Inicialización segura de estados
if 'user' not in st.session_state: st.session_state.user = None
if 'confirm_alu' not in st.session_state: st.session_state.confirm_alu = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; margin-bottom: 20px; }
    .empty-msg { padding: 30px; border-radius: 12px; background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.1); text-align: center; color: #777; margin: 10px 0; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CORREGIDO PARA ENTER) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        # Usamos un formulario nativo de Streamlit para capturar el ENTER sin errores de red
        with st.form("login_form"):
            u_input = st.text_input("Sede").strip().lower()
            p_input = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
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
    st.sidebar.write(f"Sede activa")
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

    # --- TAB 1: ALUMNOS (RECUPERADO) ---
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
                    else: st.warning("Completá nombre y apellido.")
            
            if st.session_state.confirm_alu:
                d = st.session_state.confirm_alu
                st.warning(f"¿Inscribir a {d['nom']} {d['ape']} en {d['curso']}?")
                if st.button("✅ CONFIRMAR INSCRIPCIÓN"):
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
                    except: st.error("Error al registrar en la base de datos.")
        else:
            st.markdown('<div class="empty-msg">👥 No hay cursos creados.<br>Andá a la pestaña <b>Cursos</b> para añadir tu primera materia.</div>', unsafe_allow_html=True)

    # --- TAB 0: AGENDA (CON RECORDATORIOS) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            opciones_a = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia de hoy", opciones_a)
            c_id = df_cursos[df_cursos['nombre_curso_materia'] == c_agenda.split(" | ")[0]].iloc[0]['id']
            
            # Recordatorio de tarea para hoy
            try:
                res_t = supabase.table("bitacora").select("tarea_descripcion").eq("curso_id", c_id).eq("tarea_vencimiento", str(hoy)).execute()
                if res_t.data:
                    st.markdown(f'<div class="reminder-box">🔔 <b>RECORDATORIO:</b> Para hoy había tarea:<br>{res_t.data[0]["tarea_descripcion"]}</div>', unsafe_allow_html=True)
                else: st.info("No hay tareas pendientes para revisar hoy.")
            except: pass

            with st.form("reg_clase"):
                temas = st.text_area("Temas dictados hoy:")
                tarea_n = st.text_area("Tarea para la próxima clase:")
                f_venc = st.date_input("Fecha de entrega:", hoy + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    if temas:
                        supabase.table("bitacora").insert({
                            "curso_id": int(c_id), "profesor_id": user['id'], "fecha": str(hoy),
                            "temas": temas, "tarea_descripcion": tarea_n, "tarea_vencimiento": str(f_venc),
                            "docente_nombre": user['email']
                        }).execute()
                        st.success("✅ Clase guardada.")
                    else: st.warning("Escribí los temas dictados.")
        else:
            st.markdown('<div class="empty-msg">📅 La agenda se activará cuando crees tu primer curso.</div>', unsafe_allow_html=True)

    # --- TAB ASISTENCIA Y NOTAS (CON LEYENDAS) ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            st.markdown(f'<div class="empty-msg">🚫 Esta sección requiere alumnos inscritos.<br>Inscribí al menos un alumno en la pestaña <b>Alumnos</b> para habilitarla.</div>', unsafe_allow_html=True)

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
