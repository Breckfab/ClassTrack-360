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

# --- ESTILO CSS (DISEÑO DEGRADADO DEEP OCEAN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .login-box { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; margin-bottom: 10px; }
    .reminder-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .history-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 0.9rem; }
    .info-card { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_final_v31"):
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
    with st.sidebar:
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de Cursos Segura
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: st.info("🏗️ Crea una materia primero.")
        else:
            m_age = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_age_v31")
            c_a, c_b = st.columns(2)
            with c_a:
                with st.form("f_age_v31"):
                    t1 = st.text_area("Temas dictados hoy")
                    t2 = st.text_area("Tarea próxima")
                    f2 = st.date_input("Fecha:", value=ahora + datetime.timedelta(days=7))
                    if st.form_submit_button("Guardar"):
                        if t1:
                            txt = f"[{f2.strftime('%d/%m/%Y')}] {t2}"
                            supabase.table("bitacora").insert({"profesor_id": u_data['id'], "materia": m_age, "fecha": str(ahora.date()), "temas_dictados": t1, "tarea_proxima": txt}).execute()
                            st.success("Guardado."); st.rerun()
            with c_b:
                st.write("### Historial")
                try:
                    r_h = supabase.table("bitacora").select("*").eq("materia", m_age).order("fecha", desc=True).limit(3).execute()
                    if r_h and r_h.data:
                        for e in r_h.data: st.markdown(f'<div class="history-card">📅 {e["fecha"]}<br>{e["temas_dictados"]}</div>', unsafe_allow_html=True)
                    else: st.write("Sin registros.")
                except: st.write("Error al cargar historial.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Alumnos")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_alu = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_alu_v31")
            r_alu = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_alu).not_.is_("alumno_id", "null").execute()
            if r_alu and r_alu.data:
                for x in r_alu.data:
                    if x.get('alumnos'):
                        alu = x['alumnos']
                        with st.expander(f"👤 {alu.get('apellido')}, {alu.get('nombre')}"):
                            if st.button("Dar de Baja", key=f"bj_{x['id']}"):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            with st.expander("➕ Inscribir Alumno"):
                with st.form("f_ins_v31"):
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("Inscribir"):
                        res_a = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_alu, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if df_cursos.empty: st.warning("Crea una materia.")
        else:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v31")
            sub_asis = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_asis[0]:
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                if not r_as or not r_as.data: st.info("Sin alumnos.")
                else:
                    with st.form("f_as_v31"):
                        as_list = []
                        for item in r_as.data:
                            if item and item.get('alumnos'):
                                alu = item['alumnos']
                                est = st.radio(f"{alu['apellido']}", ["Presente", "Ausente"], key=f"as_{alu['id']}", horizontal=True)
                                as_list.append({"id": alu['id'], "est": est})
                        if st.form_submit_button("Guardar"):
                            for r in as_list:
                                supabase.table("asistencia").insert({"alumno_id": r["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": r["est"]}).execute()
                            st.success("Guardado.")
            with sub_asis[1]:
                f_q = st.date_input("Fecha:", value=ahora.date())
                try:
                    r_v = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                    if r_v and r_v.data:
                        for rv in r_v.data: st.write(f"• {rv['alumnos']['apellido']}: {rv['estado']}")
                    else: st.info("Sin datos.")
                except: st.write("Error en consulta.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        if df_cursos.empty: st.warning("Crea una materia.")
        else:
            m_nt = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_nt_v31")
            r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
            if r_nt and r_nt.data:
                with st.form("f_nt_v31"):
                    inst = st.selectbox("Instancia", ["Parcial 1", "Parcial 2", "TP", "Final"])
                    nt_list = []
                    for it in r_nt.data:
                        alu = it['alumnos']
                        v = st.number_input(f"{alu['apellido']}", 1, 10, key=f"n_{alu['id']}")
                        nt_list.append({"id": alu['id'], "v": v})
                    if st.form_submit_button("Guardar"):
                        for n in nt_list:
                            supabase.table("notas").insert({"alumno_id": n["id"], "profesor_id": u_data['id'], "materia": m_nt, "tipo_nota": inst, "calificacion": n["v"], "fecha": str(ahora.date())}).execute()
                        st.success("Guardado.")
            else: st.info("Sin alumnos.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Cursos")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"📘 **{r['nombre_curso_materia']}** | {r['horario']}")
                if c2.button("Borrar", key=f"
