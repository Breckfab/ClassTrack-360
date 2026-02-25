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
    .info-card { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-top: 10px; }
    .history-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_v30"):
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
            {ahora.day} de {meses[ahora.month - 1]} de {ahora.year} | <span id="c"></span>
        </div>
        <script>
            setInterval(() => {{ 
                const d = new Date(); 
                document.getElementById('c').innerHTML = d.toLocaleTimeString('es-AR', {{hour12:false}}); 
            }}, 1000);
        </script>
    """, height=35)

    u_data = st.session_state.user
    with st.sidebar:
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de Cursos Base
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA + HISTORIAL DE CLASES ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: st.info("🏗️ Crea una materia primero.")
        else:
            m_age = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_age_v30")
            
            col_a1, col_a2 = st.columns([1, 1])
            
            with col_a1:
                st.markdown("### Nueva Entrada")
                with st.form("f_age_v30"):
                    t_hoy = st.text_area("Temas dictados hoy")
                    t_prox = st.text_area("Tarea próxima")
                    f_prox = st.date_input("Fecha de entrega:", value=ahora + datetime.timedelta(days=7))
                    if st.form_submit_button("Guardar Clase"):
                        if t_hoy:
                            t_txt = f"[{f_prox.strftime('%d/%m/%Y')}] {t_prox}"
                            supabase.table("bitacora").insert({"profesor_id": u_data['id'], "materia": m_age, "fecha": str(ahora.date()), "temas_dictados": t_hoy, "tarea_proxima": t_txt}).execute()
                            st.success("Guardado."); st.rerun()

            with col_a2:
                st.markdown("### Historial Reciente")
                try:
                    r_h = supabase.table("bitacora").select("*").eq("materia", m_age).order("fecha", desc=True).limit(5).execute()
                    if r_h and r_h.data:
                        for entry in r_h.data:
                            with st.markdown(f'<div class="history-card"><b>📅 {entry["fecha"]}</b><br>📝 {entry["temas_dictados"]}</div>', unsafe_allow_html=True):
                                pass
                    else: st.write("No hay clases registradas.")
                except: st.error("Error al cargar historial.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_alu = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_alu_v30")
            r_alu = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_alu).not_.is_("alumno_id", "null").execute()
            if r_alu and r_alu.data:
                for x in r_alu.data:
                    if x.get('alumnos'):
                        alu = x['alumnos']
                        with st.expander(f"👤 {alu.get('apellido')}, {alu.get('nombre')}"):
                            if st.button("Baja", key=f"bj_v30_{x['id']}"):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            
            with st.expander("➕ Inscribir Alumno"):
                with st.form("f_ins_v30"):
                    n_in, a_in = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Confirmar"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_in, "apellido": a_in}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_alu, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 2: ASISTENCIA + VISTA DE REGISTROS ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v30")
            sub_as = st.tabs(["📝 Tomar Asistencia", "📊 Ver Registros"])
            
            with sub_as[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if not r_as or not r_as.data: st.info("Sin alumnos.")
                else:
                    with st.form("f_as_v30"):
                        as_list = []
                        for item in r_as.data:
                            if item and item.get('alumnos'):
                                alu = item['alumnos']
                                est = st.radio(f"{alu.get('apellido')}", ["Presente", "Ausente"], key=f"as_{alu['id']}", horizontal=True)
                                as_list.append({"alumno_id": alu['id'], "estado": est})
                        if st.form_submit_button("Guardar Hoy"):
                            for r in as_list:
                                supabase.table("asistencia").insert({"alumno_id": r["alumno_id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": r["estado"]}).execute()
                            st.success("Guardado.")

            with sub_as[1]:
                f_busq = st.date_input("Consultar fecha:", value=ahora.date())
                r_v = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_busq)).execute()
                if r_v and r_v.data:
                    for rv in r_v.data:
                        st.write(f"• {rv['alumnos']['apellido']}: {rv['estado']}")
                else: st.info("No hay registros para esta fecha.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_nt = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_nt_v30")
            r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
            if r_nt and r_nt.data:
                with st.form("f_nt_v30"):
                    t_eval = st.selectbox("Instancia", ["Parcial 1", "Parcial 2", "TP", "Final"])
                    nt_list = []
                    for it in r_nt.data:
                        alu = it['alumnos']
                        v = st.number_input(f"Nota: {alu['apellido']}", 1, 10, key=f"n_{alu['id']}")
                        nt_list.append({"id": alu['id'], "v": v})
                    if st.form_submit_button("Guardar"):
                        for n in nt_list:
                            supabase.table("notas").insert({"alumno_id": n["id"], "profesor_id": u_data['id'], "materia": m_nt, "tipo_nota": t_eval, "calificacion": n["v"], "fecha": str(ahora.date())}).execute()
                        st.success("Notas guardadas.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Configuración de Materias")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"📘 **{r.get('nombre_curso_materia')}** | {r.get('horario')}")
                if c2.button("Borrar", key=f"br_v30_{r['id']}"):
                    supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                    st.rerun()
        with st.form("f_cur_v30"):
            nc, hc = st.text_input("Materia"), st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()
