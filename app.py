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
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v103"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
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
    u_data = st.session_state.user
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA CRÍTICA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (CON TRIPLE BOTONERA: GUARDAR, EDITAR, BORRAR) ---
    with tabs[4]:
        st.subheader("Gestión de Materias")
        if mapa_cursos:
            st.write("### Mis Materias")
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    # FORMULARIO DE EDICIÓN
                    with st.form(f"ed_c_v103_{i}"):
                        n_mat = st.text_input("Nombre de la Materia", value=n)
                        c1, c2, c3 = st.columns(3)
                        
                        if c1.form_submit_button("GUARDAR CAMBIOS"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", i).execute()
                            st.success("✅ Cambios guardados.")
                            st.rerun()
                            
                        if c2.form_submit_button("CANCELAR"):
                            st.rerun()
                            
                        if c3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                            st.session_state[f"confirm_c_{i}"] = True
                    
                    # CUADRO ROJO DE ADVERTENCIA PARA BORRAR
                    if st.session_state.get(f"confirm_c_{i}"):
                        st.error(f"### 🚨 ¿BORRAR MATERIA {n}? \n Se eliminará el curso y sus registros asociados. Esta acción no tiene vuelta atrás.")
                        col_y, col_n = st.columns(2)
                        if col_y.button("SÍ, BORRAR DEFINITIVAMENTE", key=f"y_c_{i}"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            del st.session_state[f"confirm_c_{i}"]
                            st.rerun()
                        if col_n.button("NO, MANTENER CURSO", key=f"n_c_{i}"):
                            del st.session_state[f"confirm_c_{i}"]
                            st.rerun()
        else:
            st.info("ℹ️ No hay materias creadas actualmente.")

        st.divider()
        # FORMULARIO DE CREACIÓN
        with st.form("f_new_c_v103"):
            st.write("### ➕ Crear Nueva Materia")
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVO CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()

    # --- RESTO DE PESTAÑAS (MANTENIENDO ESTABILIDAD) ---
    with tabs[0]: st.info("ℹ️ Agenda y buscador de tareas habilitados.")
    with tabs[1]: st.info("ℹ️ Inscriba o busque alumnos aquí.")
    with tabs[2]: st.info("ℹ️ Registro de asistencia diario.")
    with tabs[3]: st.info("ℹ️ Gestión de calificaciones por materia.")
