import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v216", layout="wide")

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
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.user is None:
    with st.form("login_v216"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 13px; color: #aaa; margin-bottom: 5px;"></div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {
                    const n = new Date();
                    document.getElementById('d').innerText = n.toLocaleDateString('es-AR');
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {hour12:false});
                }
                setInterval(update, 1000); update();
            </script>
        """, height=90)
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- DATOS SEGUROS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (CARGA RELÁMPAGO) ---
    with tabs[2]:
        st.subheader("✅ Asistencia por Curso")
        if not mapa_cursos: st.info("Cree un curso primero.")
        else:
            c_as = st.selectbox("Seleccione el curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel_v216")
            if c_as != "---":
                f_asist = st.date_input("Fecha:", datetime.date.today())
                res_l = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_l.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b></div>', unsafe_allow_html=True)
                        with st.form(f"f_asist_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            b1, b2, b3, _ = st.columns([1,1,1,5])
                            if b1.form_submit_button("💾 Guardar"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(f_asist)}).execute()
                                st.success("Cambios guardados satisfactoriamente.")
                            b2.form_submit_button("✏️ Editar")
                            b3.form_submit_button("🗑️ Borrar")

    # --- TAB 0: AGENDA (FORZAR TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_v216")
            f_hoy = st.date_input("Fecha hoy:", datetime.date.today())
            res_tarea = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_tarea.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA REVISAR HOY:<br>{res_tarea.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            with st.form("f_ag"):
                t_hoy = st.text_area("Temas")
                t_pro = st.text_area("Tarea")
                if st.form_submit_button("💾 GUARDAR"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": t_hoy, "tarea_proxima": t_pro}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()

    # --- TAB 4: CURSOS (EDICIÓN Y LISTADO) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        for c in res_c.data:
            with st.container():
                st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                cb1.button("✏️ Editar", key=f"e_cur_{c['id']}")
                if cb2.button("🗑️ Borrar", key=f"d_cur_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                cb3.button("💾 Guardar", key=f"s_cur_{c['id']}")
