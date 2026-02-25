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
        with st.form("login_v78"):
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

    # --- TAB 0: AGENDA (CON EDICIÓN COMPLETA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty: 
            st.info("🏗️ No hay materias creadas.")
        else:
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
            opts = ["--- Elegir Curso o Materia ---"] + list(mapa_cursos.keys())
            m_age = st.selectbox("Materia:", opts, key="sb_age_v78")
            
            if m_age != "--- Elegir Curso o Materia ---":
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("f_age_v78", clear_on_submit=True):
                        t1 = st.text_area("Temas dictados hoy (contenido_clase)")
                        t2 = st.text_area("Tarea próxima")
                        f2 = st.date_input("Fecha tarea:", value=ahora + datetime.timedelta(days=7))
                        if st.form_submit_button("Guardar Registro"):
                            if t1:
                                supabase.table("bitacora").insert({
                                    "inscripcion_id": mapa_cursos[m_age],
                                    "fecha": str(ahora.date()),
                                    "contenido_clase": t1,
                                    "tarea_proxima": t2
                                }).execute()
                                st.success("✅ Guardado."); st.rerun()
                
                with c2:
                    st.write("### Historial / Editar")
                    ins_id = mapa_cursos[m_age]
                    r_h = supabase.table("bitacora").select("*").eq("inscripcion_id", ins_id).order("fecha", desc=True).limit(5).execute()
                    if r_h and r_h.data:
                        for entry in r_h.data:
                            with st.expander(f"📝 Registro {entry['fecha']}"):
                                with st.form(f"edit_bit_{entry['id']}"):
                                    edit_cont = st.text_area("Editar Temas", value=entry['contenido_clase'])
                                    edit_tar = st.text_area("Editar Tarea", value=entry['tarea_proxima'] if entry['tarea_proxima'] else "")
                                    col1, col2 = st.columns(2)
                                    if col1.form_submit_button("Actualizar"):
                                        supabase.table("bitacora").update({"contenido_clase": edit_cont, "tarea_proxima": edit_tar}).eq("id", entry['id']).execute()
                                        st.rerun()
                                    if col2.form_submit_button("Eliminar"):
                                        supabase.table("bitacora").delete().eq("id", entry['id']).execute()
                                        st.rerun()

    # --- TAB 1: ALUMNOS (EDITAR DATOS PERSONALES) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        r_alu_all = supabase.table("inscripciones").select("id, alumno_id, nombre_curso_materia, alumnos(id, nombre, apellido, email)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_alu_all and r_alu_all.data:
            for x in r_alu_all.data:
                alu = x['alumnos']
                with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} ({x['nombre_curso_materia']})"):
                    with st.form(f"edit_alu_{alu['id']}"):
                        new_nom = st.text_input("Nombre", value=alu['nombre'])
                        new_ape = st.text_input("Apellido", value=alu['apellido'])
                        if st.form_submit_button("Guardar Cambios"):
                            supabase.table("alumnos").update({"nombre": new_nom, "apellido": new_ape}).eq("id", alu['id']).execute()
                            st.success("Alumno actualizado"); st.rerun()
        else: st.info("No hay alumnos.")

    # --- TAB 4: CURSOS (EDITAR NOMBRE DE MATERIA) ---
    with tabs[4]:
        st.subheader("Configuración de Cursos")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"edit_cur_{r['id']}"):
                        new_cur_nom = st.text_input("Nombre de la Materia", value=r['nombre_curso_materia'])
                        if st.form_submit_button("Cambiar Nombre"):
                            # Actualizamos el nombre en la tabla inscripciones
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_cur_nom}).eq("id", r['id']).execute()
                            st.rerun()
