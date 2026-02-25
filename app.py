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
        with st.form("login_v72"):
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

    # Carga de Materias
    df_cursos = pd.DataFrame()
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: df_cursos = pd.DataFrame(r_c.data)
    except: pass

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: 
            st.info("🏗️ No hay materias creadas.")
        else:
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
            # Cambio de etiqueta solicitado
            opts = ["--- Elegir Curso o Materia ---"] + list(mapa_cursos.keys())
            m_age = st.selectbox("Materia:", opts, key="sb_age_v72")
            
            if m_age == "--- Elegir Curso o Materia ---":
                st.info("💡 Por favor, elija un curso o materia para operar.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_age_v72", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados hoy (contenido_clase)")
                        t2 = st.text_area("Tarea próxima")
                        # Ajuste de calendario: Domingo como primer día
                        f2 = st.date_input("Fecha tarea:", 
                                         value=ahora + datetime.timedelta(days=7),
                                         format="DD/MM/YYYY")
                        
                        if st.form_submit_button("Guardar"):
                            if t1:
                                try:
                                    payload = {
                                        "inscripcion_id": mapa_cursos[m_age],
                                        "fecha": str(ahora.date()),
                                        "contenido_clase": t1,
                                        "tarea_proxima": t2 if t2 else ""
                                    }
                                    supabase.table("bitacora").insert(payload).execute()
                                    st.success("✅ Guardado en bitácora."); st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar: {str(e)}")
                with c2:
                    st.write("### Historial")
                    try:
                        ins_id = mapa_cursos[m_age]
                        r_h = supabase.table("bitacora").select("*").eq("inscripcion_id", ins_id).order("fecha", desc=True).limit(5).execute()
                        if r_h and r_h.data:
                            for entry in r_h.data:
                                with st.expander(f"📅 {entry['fecha']}"):
                                    st.write(f"**Temas:** {entry['contenido_clase']}")
                        else: st.info("ℹ️ Sin historial hasta el día de la fecha.")
                    except: st.info("ℹ️ Sin historial.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Alumnos")
        if df_cursos.empty: st.warning("Crea una materia primero.")
        else:
            m_alu = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique(), key="sb_alu_v72")
            r_alu = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_alu).not_.is_("alumno_id", "null").execute()
            if r_alu and r_alu.data:
                for x in r_alu.data:
                    if x.get('alumnos'):
                        alu = x['alumnos']
                        with st.expander(f"👤 {alu.get('apellido')}, {alu.get('nombre')}"):
                            if st.button("Baja", key=f"bj_v72_{x['id']}"):
                                supabase.table("inscripciones").delete().eq("id", x['id']).execute()
                                st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                st.write(f"📘 **{r['nombre_curso_materia']}**")
        else: st.info("🏗️ No tienes materias creadas.")
