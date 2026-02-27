import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v203", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2rem; font-weight: 800; color: #4facfe; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .reloj-sidebar { font-family: 'JetBrains Mono', monospace; color: #4facfe; font-size: 1.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGUEO ---
if st.session_state.user is None:
    st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    # --- BARRA LATERAL (RECUPERADA) ---
    with st.sidebar:
        st.markdown(f"### 🏫 Sede: {u_data['email'].split('.')[0].upper()}")
        # RELOJ Y FECHA NATIVOS
        st.divider()
        fecha_h = datetime.date.today().strftime("%d/%m/%Y")
        st.write(f"📅 **Fecha:** {fecha_h}")
        placeholder_reloj = st.empty()
        st.divider()
        if st.button("🚪 SALIR DEL SISTEMA"):
            st.session_state.user = None
            st.rerun()

    # Script simple para el reloj en sidebar
    st.components.v1.html(f"""
        <script>
        function update() {{
            const now = new Date();
            const time = now.getHours().toString().padStart(2,'0') + ":" + 
                         now.getMinutes().toString().padStart(2,'0') + ":" + 
                         now.getSeconds().toString().padStart(2,'0');
            window.parent.document.querySelector('.reloj-sidebar-container').innerText = time;
        }}
        setInterval(update, 1000);
        </script>
        <div class="reloj-sidebar-container" style="font-family: monospace; color: #4facfe; font-size: 24px; font-weight: bold;">00:00:00</div>
    """, height=40)

    # --- MOTOR DE DATOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB ALUMNOS: GESTIÓN DE DUPLICADOS ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        res_list = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        
        if res_list.data:
            for r in res_list.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b> | {r["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    # Triple botonera funcional por alumno
                    c1, c2, c3, _ = st.columns([1,1,1,5])
                    c1.button("✏️ Editar", key=f"ed_al_{r['id']}")
                    if c2.button("🗑️ Borrar", key=f"del_al_{r['id']}"):
                        # Borrado por ID único de inscripción para evitar conflictos con duplicados
                        supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                        st.success("Registro eliminado."); time.sleep(0.5); st.rerun()
                    c3.button("💾 Guardar", key=f"sav_al_{r['id']}")
        else:
            st.info("No hay alumnos registrados.")

    # --- TAB CURSOS: LISTADO Y ACCIONES ---
    with tabs[4]:
        st.subheader("🏗️ Cursos Activos")
        if res_c.data:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                bc1, bc2, _ = st.columns([1,1,6])
                if bc2.button("🗑️ Borrar Curso", key=f"dc_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                    st.rerun()
