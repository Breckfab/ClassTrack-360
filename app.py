import streamlit as st
import streamlit.components.v1 as components
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

# --- ESTILO CSS (DISEÑO DEGRADADO DEEP OCEAN + CRISTAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp { 
        background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); 
        color: #e0e0e0; 
        font-family: 'Inter', sans-serif; 
    }
    
    .login-box {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        text-align: center;
    }

    .logo-text { 
        font-weight: 800; 
        background: linear-gradient(to right, #3b82f6, #a855f7); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-bottom: 10px; 
    }
    
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; margin-bottom: 10px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE LOGIN ---
def realizar_login():
    u = st.session_state.u_final.strip().lower()
    p = st.session_state.p_final
    email_real = ""
    if u == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
    elif u == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
    
    if email_real:
        try:
            res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
            if res.data:
                st.session_state.user = res.data[0]
            else:
                st.error("usuario o contraseña incorrecta. Intente nuevamente.")
        except:
            st.error("Error de conexión. Intente nuevamente.")
    else:
        st.error("usuario o contraseña incorrecta. Intente nuevamente.")

# --- INTERFAZ ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div><p style="color:#94a3b8">Ingreso al Panel Docente</p></div>', unsafe_allow_html=True)
        st.text_input("Usuario", key="u_final", placeholder="Nombre de sede")
        st.text_input("Clave", type="password", key="p_final", placeholder="••••••••")
        st.button("Acceder al Sistema", on_click=realizar_login, use_container_width=True)
else:
    # --- RELOJ DINÁMICO BLANCO ---
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora_dt = datetime.datetime.now()
    fecha_hoy = f"{ahora_dt.day} de {meses[ahora_dt.month - 1]} de {ahora_dt.year}"
    
    components.html(f"""
        <div style="text-align: right; color: white; font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; padding-right: 10px;">
            {fecha_hoy} | <span id="clock"></span>
        </div>
        <script>
            function updateClock() {{
                const d = new Date();
                const hh = String(d.getHours()).padStart(2, '0');
                const mm = String(d.getMinutes()).padStart(2, '0');
                const ss = String(d.getSeconds()).padStart(2, '0');
                document.getElementById('clock').innerHTML = hh + ":" + mm + ":" + ss;
            }}
            setInterval(updateClock, 1000);
            updateClock();
        </script>
    """, height=35)

    user = st.session_state.user
    sede_nombre = 'Daguerre' if 'daguerre' in user['email'].lower() else 'Cambridge'
    
    with st.sidebar:
        st.write(f"📍 Sede: {sede_nombre}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de materias
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c and res_c.data:
            df_cursos = pd.DataFrame(res_c.data)
    except:
        pass

    # --- TAB 0: AGENDA (CON FLUJO PEDAGÓGICO) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            
            tarea_anterior = ""
            temas_anteriores = ""
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                if res_b and res_b.data:
                    tarea_anterior = res_b.data[0].get("tarea_proxima", "")
                    temas_anteriores = res_b.data[0].get("temas_dictados", "Sin registro")
            except:
                pass

            if tarea_anterior:
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy (de la clase anterior):</b><br>{tarea_anterior}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar hoy.</b></div>', unsafe_allow_html=True)
            
            if temas_anteriores:
                st.info(f"📍 Clase anterior: {temas_anteriores}")

            st.write("---")
            with st.form("form_agenda_completo_final"):
                t_hoy = st.text_area("Temas dictados hoy")
                t_proxima = st.text_area("Tarea para la próxima clase")
                f_proxima = st.date_input("Fecha de entrega:", value=ahora_dt + datetime.timedelta(days=7))
                
                # BOTÓN DE GUARDAR PRESENTE Y FUNCIONAL
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        try:
                            tarea_final_txt = f"[{f_proxima.strftime('%d/%m/%Y')}] {t_proxima}"
                            supabase.table("bitacora").insert({
                                "profesor_id": user['id'], 
                                "materia": c_agenda, 
                                "fecha": str(ahora_dt.date()), 
                                "temas_dictados": t_hoy, 
                                "tarea_proxima": tarea_final_txt
                            }).execute()
                            st.success("Registro guardado con éxito."); st.rerun()
                        except:
                            st.error("Error al guardar en la base de datos.")
                    else:
                        st.warning("Por favor, completa los temas dictados hoy.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Crea una materia primero.</div>', unsafe_allow_html=True)
        else:
            try:
                res_t = supabase.table("inscripciones").select("alumno_id", count="exact").eq("profesor_id", user['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
                total_m = res_t.count if res_t and res_t.count else 0
                st.markdown(f'<div class="metric-card">Matrícula {sede_nombre} 2026: <span class="metric-value">{total_m}</span></div>', unsafe_allow_html=True)
                
                mat_f = st.selectbox("Ver alumnos de:", df_cursos['nombre_curso_materia'].unique(), key="sel_alu_v_final")
                res_alu = supabase.table("inscripciones").select("alumnos(nombre, apellido)").eq("profesor_id", user['id']).eq("nombre_curso_materia", mat_f).not_.is_("alumno_id", "null").execute()
                
                if res_alu and res_alu.data:
                    for a in res_alu.data:
                        if a and 'alumnos' in a and a['alumnos']:
                            info_a = a['alumnos']
                            st.write(f"• {info_a.get('apellido', 'N/A')}, {info_a.get('nombre', 'N/A')}")
                else:
                    st.write("No hay alumnos inscritos en esta materia.")
            except:
                st.error("Error al cargar alumnos.")

            with st.expander("➕ Inscribir Estudiante"):
                with st.form("ins_alu_f_v_final"):
                    c_sel = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            try:
                                nuevo = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                                if nuevo.data:
                                    supabase.table("inscripciones").insert({
                                        "alumno_id": nuevo.data[0]['id'], 
                                        "profesor_id": user['id'], 
                                        "nombre_curso_materia": c_sel, 
                                        "anio_lectivo": 2026
                                    }).execute()
                                    st.success("Alumno inscrito."); st.rerun()
                            except:
                                st.error("Error al inscribir.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if df_cursos.empty:
            st.markdown("⚠️ Crea un curso primero.")
        else:
            mat_asis = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique(), key="asis_mat_v_final")
            try:
                res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", mat_asis).not_.is_("alumno_id", "null").execute()
                
                if not res_a or not res_a.data:
                    st.markdown('<div class="warning-card">👤 No hay alumnos inscritos.</div>', unsafe_allow_html=True)
                else:
                    st.write(f"Fecha: {ahora_dt.strftime('%d/%m/%Y')}")
                    with st.form("form_asis_v_final"):
                        datos_asistencia = []
                        for item in res_a.data:
                            if item and 'alumnos' in item and item['alumnos']:
                                alu = item['alumnos']
                                a_id = alu.get('id', 'desconocido')
                                col_a1, col_a2 = st.columns([3, 1])
                                col_a1.write(f"{alu.get('apellido', 'N/A')}, {alu.get('nombre', 'N/A')}")
                                estado = col_a2.radio("Estado:", ["Presente", "Ausente"], key=f"a_radio_{a_id}", horizontal=True)
                                datos_asistencia.append({"alumno_id": a_id, "estado": estado})
                        
                        if st.form_submit_button("Guardar Asistencia"):
                            for asis in datos_asistencia:
                                supabase.table("asistencia").insert({
                                    "alumno_id": asis["alumno_id"],
                                    "profesor_id": user['id'],
                                    "materia": mat_asis,
                                    "fecha": str(ahora_dt.date()),
                                    "estado": asis["estado"]
                                }).execute()
                            st.success("Asistencia guardada en base de datos.")
            except:
                st.error("Error al gestionar asistencia.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Planilla de Calificaciones")
        if df_cursos.empty:
            st.markdown("⚠️ Crea un curso primero.")
        else:
            mat_n = st.selectbox("Curso:", df_cursos['nombre_curso_materia'].unique(), key="notas_mat_v_final")
            try:
                res_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", mat_n).not_.is_("alumno_id", "null").execute()
                
                if not res_n or not res_n.data:
                    st.markdown('<div class="warning-card">👤 No hay alumnos para calificar.</div>', unsafe_allow_html=True)
                else:
                    with st.expander("📝 Cargar Calificaciones"):
                        with st.form("form_notas_v_final"):
                            tipo_nota = st.selectbox("Tipo de Nota:", ["Parcial 1", "Parcial 2", "Final", "Trabajo Práctico"])
                            notas_a_subir = []
                            for item in res_n.data:
                                if item and 'alumnos' in item and item['alumnos']:
                                    alu = item['alumnos']
                                    a_id = alu.get('id', 'desconocido')
                                    nota = st.number_input(f"{alu.get('apellido', 'N/A')}, {alu.get('nombre', 'N/A')}", min_value=1, max_value=10, step=1, key=f"n_val_{a_id}")
                                    notas_a_subir.append({"alumno_id": a_id, "nota": nota})
                            
                            if st.form_submit_button("Guardar Notas"):
                                for n in notas_a_subir:
                                    supabase.table("notas").insert({
                                        "alumno_id": n["alumno_id"],
                                        "profesor_id": user['id'],
                                        "materia": mat_n,
                                        "tipo_nota": tipo_nota,
                                        "calificacion": n["nota"],
                                        "fecha": str(ahora_dt.date())
                                    }).execute()
                                st.success("Notas guardadas exitosamente.")
            except:
                st.error("Error al gestionar notas.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                st.write(f"📘 **{cur.get('nombre_curso_materia', 'S/M')}** | {cur.get('horario', 'S/H')}")
        with st.form("n_c_v_final_v2"):
            nc, hc = st.text_input("Nombre de Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    try:
                        supabase.table("inscripciones").insert({
                            "profesor_id": user['id'], 
                            "nombre_curso_materia": nc, 
                            "horario": hc, 
                            "anio_lectivo": 2026
                        }).execute()
                        st.rerun()
                    except:
                        st.error("Error al crear curso.")
