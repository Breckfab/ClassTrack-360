import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v218", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO CLASSTRACK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; font-size: 1.2rem; }
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
    
    # --- SIDEBAR CON RELOJ ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html(f"""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 13px; color: #aaa;">{datetime.date.today()}</div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {{
                    const n = new Date();
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {{hour12:false}});
                }}
                setInterval(update, 1000); update();
            </script>
        """, height=90)
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS SEGURO ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON DETECTOR DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clase")
        if not mapa_cursos: st.info("Cree un curso primero en la pestaña 'Cursos'.")
        else:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_v218")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # BUSCAR TAREA PENDIENTE PARA HOY
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                for t in res_t.data:
                    st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA REVISAR HOY:<br>{t["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No se encontraron tareas pendientes para entregar hoy.")

            with st.form("f_ag_v218"):
                temas = st.text_area("Temas dictados hoy:")
                tarea_n = st.text_area("Tarea para la próxima:")
                vto = st.date_input("Fecha de entrega:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR EN BITÁCORA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea_n, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB 2: ASISTENCIA (CERO NEGRO) ---
    with tabs[2]:
        st.subheader("✅ Planilla de Asistencia")
        if mapa_cursos:
            c_as = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v218")
            if c_as != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b></div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            b1, b2, b3, _ = st.columns([1,1,1,5])
                            if b1.form_submit_button("💾 Guardar"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Cambios guardados satisfactoriamente.")
                            b2.form_submit_button("✏️ Editar")
                            b3.form_submit_button("🗑️ Borrar")

    # --- TAB 4: CURSOS (RECUPERADO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("new_cur"):
            st.write("### ➕ Instalar Nuevo Curso")
            nc = st.text_input("Materia y Horario (ej: 1ero Psicología - Lunes)")
            if st.form_submit_button("💾 GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente."); st.rerun()
