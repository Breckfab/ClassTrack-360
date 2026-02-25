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
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown('<div class="login-box"><div class="logo-text">ClassTrack 360</div></div>', unsafe_allow_html=True)
        with st.form("login_v66"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res and res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
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
        r_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA (CORRECCIÓN FINAL) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: 
            st.info("🏗️ No hay materias creadas.")
        else:
            opts = ["--- Seleccione Materia ---"] + list(df_cursos['nombre_curso_materia'].unique())
            m_age = st.selectbox("Materia:", opts, key="sb_age_v66")
            
            if m_age == "--- Seleccione Materia ---":
                st.info("💡 Por favor, elija una materia del menú para operar.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_age_v66", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados hoy")
                        t2 = st.text_area("Tarea próxima")
                        f2 = st.date_input("Fecha tarea:", value=ahora + datetime.timedelta(days=7))
                        if st.form_submit_button("Guardar Registro"):
                            if t1:
                                txt_t = f"[{f2.strftime('%d/%m/%Y')}] {t2}" if t2 else ""
                                payload = {
                                    "profesor_id": u_data['id'],
                                    "fecha": str(ahora.date()),
                                    "temas_dictados": t1,
                                    "tarea_proxima": txt_t
                                }
                                # Intentamos insertar probando las dos variantes de columna que existen en tu DB
                                try:
                                    p1 = payload.copy(); p1["nombre_materia"] = m_age
                                    supabase.table("bitacora").insert(p1).execute()
                                    st.success("✅ Guardado correctamente."); st.rerun()
                                except:
                                    try:
                                        p2 = payload.copy(); p2["materia"] = m_age
                                        supabase.table("bitacora").insert(p2).execute()
                                        st.success("✅ Guardado correctamente."); st.rerun()
                                    except Exception as e:
                                        st.error(f"Error estructural. Verifique que la tabla 'bitacora' exista. {str(e)}")
                with c2:
                    st.write("### Historial Reciente")
                    try:
                        r_h = supabase.table("bitacora").select("*").or_(f"nombre_materia.eq.{m_age},materia.eq.{m_age}").order("fecha", desc=True).limit(5).execute()
                        if r_h and r_h.data:
                            for entry in r_h.data:
                                with st.expander(f"📅 {entry['fecha']}"):
                                    st.write(f"**Temas:** {entry['temas_dictados']}")
                        else: st.info("ℹ️ Sin historial hasta el día de la fecha.")
                    except: st.info("ℹ️ Sin historial hasta el día de la fecha.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Alumnos")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_alu = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_alu_v66")
            r_alu = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_alu).not_.is_("alumno_id", "null").execute()
            if r_alu and r_alu.data:
                for x in r_alu.data:
                    if x.get('alumnos'):
                        alu = x['alumnos']
                        with st.expander(f"👤 {alu.get('apellido')}, {alu.get('nombre')}"):
                            if st.button("Baja", key=f"bj_v66_{x['id']}"):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("Asistencia")
        if df_cursos.empty: st.warning("Crea una materia.")
        else:
            m_as = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_as_v66")
            sub_asis = st.tabs(["📝 Tomar", "📊 Consultar"])
            with sub_asis[1]:
                f_q = st.date_input("Fecha:", value=ahora.date(), key="f_as_v66")
                try:
                    rv = supabase.table("asistencia").select("estado, alumnos(nombre, apellido)").eq("materia", m_as).eq("fecha", str(f_q)).execute()
                    if rv and rv.data:
                        for r in rv.data: st.write(f"• {r['alumnos']['apellido']}: {r['estado']}")
                    else: st.info("ℹ️ Sin datos para esta fecha.")
                except: st.info("ℹ️ Sin datos para esta fecha.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("Notas")
        if df_cursos.empty: st.warning("Crea una materia.")
        else:
            m_nt = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_nt_v66")
            sub_nt = st.tabs(["📝 Cargar", "🔍 Consultar"])
            with sub_nt[1]:
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if r_al_n and r_al_n.data:
                    op_n = {f"{it['alumnos']['apellido']}, {it['alumnos']['nombre']}": it['alumnos']['id'] for it in r_al_n.data}
                    sel_n = st.selectbox("Alumno:", list(op_n.keys()), key="sel_nt_v66")
                    if st.button("Buscar"):
                        id_a_n = op_n[sel_n]
                        rh_n = supabase.table("notas").select("id, fecha, tipo_nota, calificacion").eq("alumno_id", id_a_n).eq("materia", m_nt).order("fecha", desc=True).execute()
                        if rh_n and rh_n.data:
                            for h in rh_n.data: st.write(f"📅 {h['fecha']} | **{h['tipo_nota']}**: {h['calificacion']}")
                        else: st.info("ℹ️ Sin registros.")
                else: st.info("ℹ️ Sin alumnos.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"📘 **{r['nombre_curso_materia']}**")
                if c2.button("Borrar", key=f"br_v66_{r['id']}"):
                    supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                    st.rerun()
        else: st.info("🏗️ No tienes materias creadas.")
