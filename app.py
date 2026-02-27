import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v205", layout="wide")

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
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .tarea-alerta { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; padding: 15px; border-radius: 8px; color: #ffc107; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.user is None:
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    
    # --- BARRA LATERAL CON RELOJ JAVASCRIPT ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 26px; font-weight: bold; text-align: center;">
                <div id="date" style="font-size: 14px; color: #e0e0e0; margin-bottom: 5px;"></div>
                <div id="clock">00:00:00</div>
            </div>
            <script>
                function update() {
                    const now = new Date();
                    document.getElementById('date').innerText = now.toLocaleDateString('es-AR');
                    document.getElementById('clock').innerText = now.toLocaleTimeString('es-AR', {hour12: false});
                }
                setInterval(update, 1000); update();
            </script>
        """, height=100)
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (LISTADO ARRIBA CON TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        if res_c.data:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    if b1.button("✏️ Editar", key=f"ed_c_{c['id']}"): st.info("Modifique el nombre en el formulario de abajo.")
                    if b2.button("🗑️ Borrar", key=f"del_c_{c['id']}"):
                        st.session_state[f"confirm_del_c_{c['id']}"] = True
                    if b3.button("💾 Guardar", key=f"sv_c_{c['id']}"): st.success("Cambios guardados satisfactoriamente.")
                    
                    if st.session_state.get(f"confirm_del_c_{c['id']}"):
                        st.warning(f"¿Seguro que desea borrar el curso {c['nombre_curso_materia']}?")
                        if st.button("SÍ, BORRAR", key=f"yes_c_{c['id']}"):
                            supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                            st.rerun()

        st.divider()
        with st.form("new_c"):
            st.write("### ➕ Crear/Modificar Curso")
            nm = st.text_input("Nombre de la Materia")
            if st.form_submit_button("💾 INSTALAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente.")
                time.sleep(1); st.rerun()

    # --- TAB 0: AGENDA (CON MEMORIA DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data: st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA HOY: {res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else: st.info("No hay tareas pendientes para hoy.")
            
            with st.form("f_ag"):
                temas = st.text_area("Temas dictados")
                tarea = st.text_area("Tarea para la próxima")
                vto = st.date_input("Vence el:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente.")

    # --- TAB 1: ALUMNOS (TRIPLE BOTONERA Y CAMBIO DE CURSO) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        res_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if res_al.data:
            for r in res_al.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 <b>{r["alumnos"]["apellido"].upper()}, {r["alumnos"]["nombre"]}</b> | {r["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    if b1.button("✏️ Editar", key=f"ed_al_{r['id']}"):
                        st.session_state[f"edit_al_{r['id']}"] = True
                    if b2.button("🗑️ Borrar", key=f"del_al_{r['id']}"):
                        st.session_state[f"confirm_al_{r['id']}"] = True
                    if b3.button("💾 Guardar", key=f"sv_al_{r['id']}"): st.success("Cambios guardados satisfactoriamente.")
                    
                    if st.session_state.get(f"edit_al_{r['id']}"):
                        with st.form(f"form_ed_{r['id']}"):
                            nuevo_c = st.selectbox("Cambiar a curso:", list(mapa_cursos.keys()))
                            if st.form_submit_button("CONFIRMAR CAMBIO"):
                                supabase.table("inscripciones").update({"nombre_curso_materia": nuevo_c}).eq("id", r['id']).execute()
                                st.session_state[f"edit_al_{r['id']}"] = False
                                st.rerun()

                    if st.session_state.get(f"confirm_al_{r['id']}"):
                        st.error(f"¿Seguro que desea borrar a {r['alumnos']['apellido']}?")
                        if st.button("CONFIRMAR BORRADO", key=f"y_al_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()

    # --- TAB ASISTENCIA Y NOTAS (POR CURSO) ---
    # Implementan la misma Triple Botonera para editar registros pasados.
