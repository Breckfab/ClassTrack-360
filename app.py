import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v198", layout="wide")

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
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    .tarea-alerta { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #ffc107; text-align: center; border: 1px dashed #ffc107; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ Y FECHA ---
components.html("""
    <div id="info-superior">
        <div id="fecha-actual" style="font-size: 0.9rem; color: #e0e0e0;">--/--/----</div>
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
        window.parent.document.getElementById('fecha-actual').innerText = d + '/' + m + '/' + a;
        window.parent.document.getElementById('reloj-fijo').innerText = h + ':' + min + ':' + s;
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

    # --- TAB ASISTENCIA (POR CURSO) ---
    with tabs[2]:
        st.subheader("✅ Toma de Asistencia")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_as = st.selectbox("Seleccione el curso para tomar lista:", ["---"] + list(mapa_cursos.keys()), key="as_sel")
            if c_as != "---":
                res_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for item in res_as.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}_{c_as}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 REGISTRAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Registrado.")

    # --- TAB NOTAS (POR CURSO CON PROMEDIO) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Notas")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_nt = st.selectbox("Seleccione el curso para ver notas:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
            if c_nt != "---":
                res_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                for item in res_nt.data:
                    al = item['alumnos']
                    hist_n = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", c_nt).execute()
                    notas_val = [float(n['calificacion']) for n in hist_n.data]
                    prom = sum(notas_val)/len(notas_val) if notas_val else 0.0
                    
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}</b>, {al["nombre"]} <span style="float:right;">Promedio: <span class="promedio-badge">{prom:.2f}</span></span></div>', unsafe_allow_html=True)
                        with st.form(f"f_nt_{al['id']}_{c_nt}"):
                            # Nota manual empezando en 7.0 o vacía
                            n_nueva = st.number_input("Ingresar Nota (ej: 7.00):", min_value=1.0, max_value=10.0, value=7.0, step=0.1, format="%.2f")
                            if st.form_submit_button("💾 VOLCAR NOTA"):
                                supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_nt, "calificacion": n_nueva, "fecha": str(datetime.date.today())}).execute()
                                st.rerun()

    # --- TAB AGENDA (TAREA PARA HOY) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            
            # Buscar tarea que se programó para HOY en este curso
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 <b>TAREA PARA ENTREGAR HOY:</b><br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="tarea-alerta">✅ No hay tareas pendientes para hoy en este curso.</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_v198"):
                tema = st.text_area("¿Qué temas se dieron hoy?")
                t_fut = st.text_area("Tarea para la clase que viene:")
                f_fut = st.date_input("Fecha de entrega de esta tarea:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 CERRAR CLASE"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": tema, "tarea_proxima": t_fut, "fecha_tarea": str(f_fut)}).execute()
                    st.success("Bitácora guardada.")

    # --- TAB ALUMNOS Y CURSOS ---
    # Mantienen la lógica de edición/borrado directo sin códigos.
