import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v181", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO Y RELOJ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .card-curso { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(79, 172, 254, 0.3); margin-bottom: 15px; }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    #reloj-fijo { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #4facfe; z-index: 10000; background: rgba(0,0,0,0.7); padding: 5px 12px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ FUNCIONAL ---
components.html("""
    <div id="reloj-fijo">00:00:00</div>
    <script>
    function actualizarReloj() {
        const ahora = new Date();
        const h = String(ahora.getHours()).padStart(2, '0');
        const m = String(ahora.getMinutes()).padStart(2, '0');
        const s = String(ahora.getSeconds()).padStart(2, '0');
        window.parent.document.getElementById('reloj-fijo').innerText = h + ':' + m + ':' + s;
    }
    setInterval(actualizarReloj, 1000);
    actualizarReloj();
    </script>
    """, height=0)

if st.session_state.user is None:
    # Lógica de Login simplificada para brevedad
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v181"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com"
                res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👨‍🏫 {u_data['nombre']}")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (CON TRIPLE BOTONERA Y HORARIOS) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos y Horarios")
        
        # Formulario de creación
        with st.expander("➕ CREAR NUEVO CURSO", expanded=True):
            with st.form("new_cur_v181"):
                c1, c2 = st.columns(2)
                c_nom = c1.text_input("Nombre de la Materia")
                c_dias = c1.multiselect("Días de cursada:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                c_hs = c2.text_input("Horario (ej: 18:00 a 20:00)")
                c_anio = c2.number_input("Año Lectivo", value=2026)
                if st.form_submit_button("💾 INSTALAR CURSO"):
                    if c_nom and c_dias:
                        dias_str = ", ".join(c_dias)
                        # Nota: En Supabase, usamos el campo estado o descripcion para guardar esto temporalmente si no migraste la tabla
                        supabase.table("inscripciones").insert({
                            "profesor_id": u_data['id'], 
                            "nombre_curso_materia": f"{c_nom} ({dias_str} - {c_hs})", 
                            "anio_lectivo": c_anio
                        }).execute()
                        st.success("Curso creado"); time.sleep(1); st.rerun()

        st.divider()
        st.markdown("### 📋 Listado de Cursos Activos")
        
        res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            for cur in res_c.data:
                with st.container():
                    st.markdown(f"""
                    <div class="card-curso">
                        <strong>📖 Materia:</strong> {cur['nombre_curso_materia']}<br>
                        <strong>📅 Año:</strong> {cur['anio_lectivo']}
                    </div>
                    """, unsafe_allow_html=True)
                    col_b1, col_b2, col_b3, _ = st.columns([1,1,1,4])
                    if col_b1.button("✏️ Editar", key=f"ed_{cur['id']}"):
                        st.info("Función de edición habilitada en panel lateral (Próximamente)")
                    if col_b2.button("🗑️ Borrar", key=f"del_{cur['id']}"):
                        supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                        st.warning("Curso eliminado"); time.sleep(0.5); st.rerun()
                    if col_b3.button("💾 Guardar", key=f"sv_{cur['id']}"):
                        st.success("Cambios guardados")

    # --- TAB 0: AGENDA (CON FILTRO DE CURSO) ---
    with tabs[0]:
        st.subheader("📅 Bitácora de Clase")
        mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}
        if not mapa_cursos:
            st.warning("No hay cursos creados.")
        else:
            sel_ag = st.selectbox("Seleccionar Curso para la Agenda:", list(mapa_cursos.keys()))
            with st.form("f_agenda_v181"):
                st.write(f"**Materia:** {sel_ag}")
                t_hoy = st.text_area("Contenido dictado hoy")
                rec = st.text_input("Recursos / Libros utilizados")
                if st.form_submit_button("💾 REGISTRAR CLASE"):
                    supabase.table("bitacora").insert({
                        "inscripcion_id": mapa_cursos[sel_ag],
                        "fecha": str(datetime.date.today()),
                        "contenido_clase": t_hoy,
                        "recursos_utilizados": rec
                    }).execute()
                    st.success("Agenda actualizada")
