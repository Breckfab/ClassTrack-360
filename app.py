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
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; margin-bottom: 20px; }
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .print-area { background-color: white; color: black; padding: 25px; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd; }
    @media print { .no-print { display: none !important; } .stApp { background-color: white !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (VALIDADO PARA ENTER Y BOTÓN) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_final"):
            u_input = st.text_input("Usuario").strip().lower()
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
                        else: st.error("Credenciales incorrectas.")
                    except: st.error("Error de conexión. Reintenta.")
                else: st.error("Usuario no reconocido.")
else:
    user = st.session_state.user
    hoy = datetime.datetime.now()
    es_daguerre = "daguerre" in user['email'].lower()
    
    st.sidebar.write(f"Sesión: {'Daguerre' if es_daguerre else 'Cambridge'}")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CARGA MAESTRA DE CURSOS ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 0: AGENDA (CON MEMORIA INTELIGENTE) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Continuidad")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas. Ve a la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia de hoy:", df_cursos['nombre_curso_materia'].unique())
            
            ultima_clase = None
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b.data: ultima_clase = res_b.data[0]
            except: pass

            if ultima_clase:
                tarea_revisar = ultima_clase.get('tarea_proxima', 'No se asignó tarea.')
                temas_pasados = ultima_clase.get('temas_dictados', 'No hay registros anteriores.')
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{tarea_revisar}</div>', unsafe_allow_html=True)
                st.info(f"📍 **La clase anterior viste:** {temas_pasados}")
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar.</b> Es el primer registro para esta materia.</div>', unsafe_allow_html=True)

            with st.form("form_agenda_hoy", clear_on_submit=True):
                st.write(f"📝 **Registro para hoy: {hoy.strftime('%d/%m/%Y')}**")
                temas_h = st.text_area("¿Qué temas vas a dictar hoy?")
                tarea_h = st.text_area("Tarea para la próxima clase:")
                if st.form_submit_button("Guardar Clase"):
                    if temas_h:
                        supabase.table("bitacora").insert({
                            "profesor_id": user['id'], "materia": c_agenda, "fecha": str(hoy.date()),
                            "temas_dictados": temas_h, "tarea_proxima": tarea_h
                        }).execute()
                        st.success("¡Clase guardada!")
                        st.rerun()
                    else: st.warning("Escribí los temas de hoy.")

    # --- TAB 1: ALUMNOS (BÚSQUEDA E INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("Búsqueda e Inscripción")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero para inscribir alumnos.</div>', unsafe_allow_html=True)
        else:
            busq_alu = st.text_input("🔍 Buscar Alumno por Apellido")
            with st.expander("➕ Inscribir Estudiante", expanded=True):
                with st.form("ins_alu_f", clear_on_submit=True):
                    c_sel = st.selectbox("Asignar a:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
                    nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if nom and ape:
                            nuevo = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape}).execute()
                            c_nom, c_hor = c_sel.split(" | ")
                            supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_nom, "horario": c_hor, "anio_lectivo": 2026}).execute()
                            st.success("Alumno anotado."); st.rerun()

    # --- TAB 2 Y 3: ASISTENCIA Y NOTAS ---
    for i, label in [(2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            if df_cursos.empty:
                st.markdown(f'<div class="warning-card">⚠️ Crea un curso primero para ver {label}.</div>', unsafe_allow_html=True)
            else:
                mat_sel = st.selectbox(f"Materia para {label}:", df_cursos['nombre_curso_materia'].unique(), key=f"sel_{i}")
                res_check = supabase.table("inscripciones").select("alumno_id").eq("nombre_curso_materia", mat_sel).not_.is_("alumno_id", "null").execute()
                
                if not res_check.data:
                    st.markdown(f'<div class="warning-card">👤 <b>No hay alumnos registrados aún en {mat_sel}.</b><br>Inscribilos en la pestaña <b>Alumnos</b> primero.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warning-card">📝 <b>No hay {label} disponibles para mostrar todavía.</b><br>Podés empezar a cargar datos en esta sección.</div>', unsafe_allow_html=True)

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows(): st.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']}")
        with st.form("nuevo_c_f"):
            nc, hc = st.text_input("Nombre de Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear Materia"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
