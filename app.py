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

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .login-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; margin-bottom: 10px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .info-card { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #3b82f6; padding: 20px; border-radius: 8px; margin-top: 10px; }
    .warning-card { background: rgba(255, 184, 0, 0.1); border-left: 5px solid #ffb800; padding: 15px; border-radius: 8px; color: #ffb800; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_final_v24"):
            u_in = st.text_input("Sede (ej. cambridge)").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede inválida.")
else:
    # --- RELOJ ---
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    ahora = datetime.datetime.now()
    components.html(f"""
        <div style="text-align: right; color: white; font-family: 'Inter'; font-size: 16px;">
            {ahora.day} de {meses[ahora.month - 1]} de {ahora.year} | <span id="c"></span>
        </div>
        <script>
            setInterval(() => {{ 
                const d = new Date(); 
                document.getElementById('c').innerHTML = d.toLocaleTimeString('es-AR', {{hour12:false}}); 
            }}, 1000);
        </script>
    """, height=35)

    u_info = st.session_state.user
    sede_activa = 'Daguerre' if 'daguerre' in u_info['email'].lower() else 'Cambridge'
    with st.sidebar:
        st.write(f"📍 Sede: {sede_activa}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de Cursos
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", u_info['id']).is_("alumno_id", "null").execute()
        if r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_age_v24")
            try:
                r_b = supabase.table("bitacora").select("tarea_proxima").eq("materia", m_agenda).order("fecha", desc=True).limit(1).execute()
                if r_b.data: st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy:</b><br>{r_b.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar hoy.</b></div>', unsafe_allow_html=True)
            except: pass

            with st.form("form_registro_clase_v24"):
                t_hoy = st.text_area("Temas dictados hoy")
                t_prox = st.text_area("Tarea próxima")
                f_prox = st.date_input("Fecha de entrega:", value=ahora + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        try:
                            t_txt = f"[{f_prox.strftime('%d/%m/%Y')}] {t_prox}"
                            supabase.table("bitacora").insert({"profesor_id": u_info['id'], "materia": m_agenda, "fecha": str(ahora.date()), "temas_dictados": t_hoy, "tarea_proxima": t_txt}).execute()
                            st.success("Guardado."); st.rerun()
                        except: st.error("Error al guardar.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_sel = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_alu_v24")
            r_alu = supabase.table("inscripciones").select("id, alumno_id, alumnos(nombre, apellido)").eq("nombre_curso_materia", m_sel).not_.is_("alumno_id", "null").execute()
            
            if r_alu.data:
                for x in r_alu.data:
                    if x.get('alumnos'):
                        alu = x['alumnos']
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']}"):
                            c1, c2 = st.columns([2, 1])
                            m_trans = c1.selectbox("Cambiar a:", df_cursos['nombre_curso_materia'].unique(), key=f"tr_{x['id']}")
                            if c1.button("Transferir", key=f"btn_tr_{x['id']}"):
                                supabase.table("inscripciones").update({"nombre_curso_materia": m_trans}).eq("id", x['id']).execute()
                                st.rerun()
                            if c2.button("Eliminar Registro", key=f"bj_{x['id']}", use_container_width=True):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            else: st.markdown('<div class="info-card">ℹ️ No hay alumnos inscritos en esta materia.</div>', unsafe_allow_html=True)

            with st.expander("➕ Inscribir Nuevo Alumno"):
                with st.form("f_nuevo_alu_v24"):
                    n_in, a_in = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n_in and a_in:
                            res_new = supabase.table("alumnos").insert({"nombre": n_in, "apellido": a_in}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": res_new.data[0]['id'], "profesor_id": u_info['id'], "nombre_curso_materia": m_sel, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 2: ASISTENCIA (CON LEYENDAS) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ Debes crear una materia antes de tomar asistencia.</div>', unsafe_allow_html=True)
        else:
            m_asis = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_asis_v24")
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_asis).not_.is_("alumno_id", "null").execute()
            
            if not r_as.data:
                st.markdown('<div class="info-card">👤 <b>No hay alumnos inscritos en esta materia.</b><br>Ve a la pestaña "Alumnos" para registrar estudiantes.</div>', unsafe_allow_html=True)
            else:
                st.write(f"Fecha: {ahora.strftime('%d
