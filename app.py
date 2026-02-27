import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v212", layout="wide")

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
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-size: 1.1rem; font-weight: bold; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.user is None:
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    
    # --- BARRA LATERAL (RELOJ JS) ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 26px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 14px; color: #888; margin-bottom: 5px;"></div>
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
        """, height=100)
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS SEGURO ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (REPARADO - FILTRO OBLIGATORIO) ---
    with tabs[2]:
        st.subheader("✅ Planilla de Asistencia")
        if not mapa_cursos:
            st.info("Debe crear un curso primero en la pestaña 'Cursos'.")
        else:
            c_as_sel = st.selectbox("Elija el curso para tomar asistencia:", ["---"] + list(mapa_cursos.keys()), key="as_sel_v212")
            
            if c_as_sel != "---":
                f_asist = st.date_input("Fecha de Asistencia:", datetime.date.today())
                # Traer solo alumnos de este curso
                res_al_asist = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as_sel).not_.is_("alumno_id", "null").execute()
                
                if not res_al_asist.data:
                    st.warning("No hay alumnos inscriptos en este curso.")
                else:
                    for r in res_al_asist.data:
                        al = r['alumnos']
                        with st.container():
                            st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b></div>', unsafe_allow_html=True)
                            with st.form(f"f_asist_v212_{al['id']}"):
                                estado = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                b1, b2, b3, _ = st.columns([1,1,1,5])
                                if b1.form_submit_button("💾 Guardar"):
                                    supabase.table("asistencia").insert({
                                        "alumno_id": al['id'], 
                                        "profesor_id": u_data['id'], 
                                        "materia": c_as_sel, 
                                        "estado": estado, 
                                        "fecha": str(f_asist)
                                    }).execute()
                                    st.success("Cambios guardados satisfactoriamente.")
                                b2.form_submit_button("✏️ Editar")
                                b3.form_submit_button("❌ Borrar")

    # --- TAB 0: AGENDA (CON DETECTOR ACTIVO) ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clase")
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_v212")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # Buscar si hay tarea para hoy
            res_tarea = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_tarea.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA REVISAR HOY:<br>{res_tarea.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_v212"):
                temas = st.text_area("Temas dictados hoy:")
                n_tarea = st.text_area("Tarea para la próxima:")
                vto = st.date_input("Fecha de vencimiento:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()

    # --- TAB 1, 3 Y 4 SE MANTIENEN ESTABLES ---
