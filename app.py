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
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; margin-bottom: 10px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_v21"):
            u_in = st.text_input("Sede").strip().lower()
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
            {ahora.day} de {meses[ahora.month - 1]} | <span id="c"></span>
        </div>
        <script>
            setInterval(() => {{ 
                const d = new Date(); 
                document.getElementById('c').innerHTML = d.toLocaleTimeString('es-AR', {{hour12:false}}); 
            }}, 1000);
        </script>
    """, height=35)

    u_data = st.session_state.user
    sede = 'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'
    with st.sidebar:
        st.write(f"📍 Sede: {sede}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de Cursos
    df_c = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: df_c = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_c.empty: st.warning("Crea una materia primero.")
        else:
            mat = st.selectbox("Materia:", df_c['nombre_curso_materia'].unique(), key="sb_age_v21")
            try:
                r_b = supabase.table("bitacora").select("tarea_proxima").eq("materia", mat).order("fecha", desc=True).limit(1).execute()
                if r_b.data: st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para Hoy:</b><br>{r_b.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            except: pass

            with st.form("f_age_v21"):
                t1 = st.text_area("Temas de hoy")
                t2 = st.text_area("Tarea próxima")
                f2 = st.date_input("Fecha:", value=ahora + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar"):
                    if t1:
                        txt = f"[{f2.strftime('%d/%m/%Y')}] {t2}"
                        supabase.table("bitacora").insert({"profesor_id": u_data['id'], "materia": mat, "fecha": str(ahora.date()), "temas_dictados": t1, "tarea_proxima": txt}).execute()
                        st.success("Guardado."); st.rerun()

    # --- TAB 1: ALUMNOS (MOVILIDAD Y BAJAS) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_c.empty: st.warning("Crea una materia primero.")
        else:
            m_f = st.selectbox("Materia Origen:", df_c['nombre_curso_materia'].unique(), key="sb_alu_v21")
            r_a = supabase.table("inscripciones").select("id, alumno_id, alumnos(nombre, apellido)").eq("nombre_curso_materia", m_f).not_.is_("alumno_id", "null").execute()
            
            if r_a.data:
                for x in r_a.data:
                    if x.get('alumnos'):
                        with st.expander(f"👤 {x['alumnos']['apellido']}, {x['alumnos']['nombre']}"):
                            col1, col2 = st.columns([2, 1])
                            # Opción de cambio de curso
                            m_destino = col1.selectbox("Cambiar a:", df_c['nombre_curso_materia'].unique(), key=f"move_{x['id']}")
                            if col1.button("Transferir Alumno", key=f"btn_move_{x['id']}"):
                                supabase.table("inscripciones").update({"nombre_curso_materia": m_destino}).eq("id", x['id']).execute()
                                st.success(f"Transferido a {m_destino}")
                                st.rerun()
                            
                            # Opción de baja definitiva
                            if col2.button("Dar de Baja", key=f"del_alu_{x['id']}", use_container_width=True):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            else: st.info("No hay alumnos en esta materia.")

            with st.expander("➕ Inscribir Alumno Nuevo"):
                with st.form("f_ins_v21"):
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        if n and a:
                            alu = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": alu.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_f, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if not df_c.empty:
            m_asis = st.selectbox("Materia:", df_c['nombre_curso_materia'].unique(), key="sb_asis_v21")
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_asis).not_.is_("alumno_id", "null").execute()
            if r_as.data:
                with st.form("f_as_v21"):
                    for item in r_as.data:
                        if item.get('alumnos'):
                            alu_obj = item['alumnos']
                            st.radio(f"{alu_obj['apellido']}, {alu_obj['nombre']}", ["Presente", "Ausente"], key=f"as_r_{alu_obj['id']}", horizontal=True)
                    if st.form_submit_button("Guardar"): st.success("Asistencia tomada.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        if not df_c.empty:
            m_nota = st.selectbox("Materia:", df_c['nombre_curso_materia'].unique(), key="sb_nota_v21")
            r_ns = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nota).not_.is_("alumno_id", "null").execute()
            if r_ns.data:
                with st.form("f_nota_v21"):
                    for item in r_ns.data:
                        if item.get('alumnos'):
                            alu_obj = item['alumnos']
                            st.number_input(f"Nota: {alu_obj['apellido']}", 1, 10, key=f"nt_v_{alu_obj['id']}")
                    if st.form_submit_button("Guardar"): st.success("Notas guardadas.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_c.empty:
            for _, r in df_c.iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{r['nombre_curso_materia']}** | {r['horario']}")
                if col_c2.button("Eliminar", key=f"del_cur_{r['id']}"):
                    supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                    st.rerun()
        
        with st.form("f_cur_v21"):
            nc, hc = st.text_input("Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear Materia"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
