import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v194", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO, RELOJ Y FECHA (RECUPERADOS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# RELOJ Y FECHA DINÁMICOS
components.html("""
    <div id="info-superior">
        <div id="fecha-actual" style="font-size: 0.9rem; color: #e0e0e0;">Cargando...</div>
        <div id="reloj-fijo" style="font-size: 1.2rem; color: #4facfe; font-weight: bold;">00:00:00</div>
    </div>
    <script>
    function actualizarInfo() {
        const ahora = new Date();
        const d = String(ahora.getDate()).padStart(2, '0');
        const m = String(ahora.getMonth() + 1).padStart(2, '0');
        const a = ahora.getFullYear();
        const h = String(ahora.getHours()).padStart(2, '0');
        const min = String(ahora.getMinutes()).padStart(2, '0');
        const s = String(ahora.getSeconds()).padStart(2, '0');
        const fechaStr = d + '/' + m + '/' + a;
        const relojStr = h + ':' + min + ':' + s;
        window.parent.document.getElementById('fecha-actual').innerText = fechaStr;
        window.parent.document.getElementById('reloj-fijo').innerText = relojStr;
    }
    setInterval(actualizarInfo, 1000); actualizarInfo();
    </script>
    """, height=60)

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
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON CALENDARIO Y TAREAS) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clases")
        if not mapa_cursos:
            st.warning("⚠️ Sin cursos creados.")
        else:
            c_sel = st.selectbox("Seleccionar Curso:", list(mapa_cursos.keys()))
            f_agenda = st.date_input("Fecha de la clase (Calendario):", datetime.date.today())
            
            # Recuperar datos de esa fecha
            res_ag = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[c_sel]).eq("fecha", str(f_agenda)).execute()
            
            with st.form("form_ag_v194"):
                t_hoy = st.text_area("Temas dictados hoy:", value=res_ag.data[0]['contenido_clase'] if res_ag.data else "")
                t_proxima = st.text_area("Tarea para la próxima fecha:", value=res_ag.data[0]['tarea_proxima'] if res_ag.data else "")
                f_vto = st.date_input("Fecha de entrega de esta tarea:", datetime.date.today() + datetime.timedelta(days=7))
                
                b1, b2, b3, _ = st.columns([1,1,1,3])
                if b1.form_submit_button("💾 GUARDAR"):
                    payload = {"inscripcion_id": mapa_cursos[c_sel], "fecha": str(f_agenda), "contenido_clase": t_hoy, "tarea_proxima": t_proxima, "fecha_tarea": str(f_vto)}
                    if res_ag.data:
                        supabase.table("bitacora").update(payload).eq("id", res_ag.data[0]['id']).execute()
                    else:
                        supabase.table("bitacora").insert(payload).execute()
                    st.success("Satisactorio."); st.rerun()
                b2.form_submit_button("✏️ EDITAR")
                b3.form_submit_button("❌ BORRAR")

    # --- TAB 3: NOTAS (RECUPERADO) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Calificaciones")
        res_n = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if not res_n.data:
            st.info("No hay alumnos cargados para poner notas.")
        else:
            for r in res_n.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]} <small>({r["nombre_curso_materia"]})</small></div>', unsafe_allow_html=True)
                    with st.form(f"n_{r['id']}"):
                        nota = st.number_input("Calificación:", 1.0, 10.0, step=0.5)
                        if st.form_submit_button("💾 GUARDAR NOTA"):
                            supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "calificacion": nota, "fecha": str(datetime.date.today())}).execute()
                            st.success("Nota guardada.")

    # --- TAB 4: CURSOS (NUEVO CURSO HABILITADO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("new_c_v194"):
            st.write("### ➕ Crear Nuevo Curso")
            nc = st.text_input("Nombre de la Materia / Horario")
            if st.form_submit_button("💾 GUARDAR CURSO"):
                if nc:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                    st.success("Curso creado."); time.sleep(0.5); st.rerun()
        
        st.divider()
        if res_c.data:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                if st.button("🗑️ Borrar", key=f"del_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                    st.rerun()
