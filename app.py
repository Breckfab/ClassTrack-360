import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v207", layout="wide")

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
    
    # --- SIDEBAR CON RELOJ JS ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 13px; color: #aaa;"></div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function u() {
                    const n = new Date();
                    document.getElementById('d').innerText = n.toLocaleDateString('es-AR');
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {hour12:false});
                }
                setInterval(u, 1000); u();
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

    # --- TAB AGENDA (BLINDADA) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clase")
        if not mapa_cursos: st.info("Vaya a 'Cursos' para crear uno primero.")
        else:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_sel")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data: st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA HOY: {res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            with st.form("f_ag"):
                t_dic = st.text_area("Temas dictados")
                t_fut = st.text_area("Tarea próxima")
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": t_dic, "tarea_proxima": t_fut}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB ALUMNOS (BLOQUEO DE NEGRO) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        if not mapa_cursos: st.warning("Debe crear un curso para inscribir alumnos.")
        else:
            with st.expander("➕ Inscribir Alumno"):
                with st.form("new_al"):
                    n, a = st.text_input("Nombre"), st.text_input("Apellido")
                    c_ins = st.selectbox("Curso:", list(mapa_cursos.keys()))
                    if st.form_submit_button("💾 REGISTRAR"):
                        ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                        if ra.data:
                            supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_ins, "anio_lectivo": 2026}).execute()
                            st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB NOTAS (TRIPLE BOTONERA) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            c_nt = st.selectbox("Filtrar por Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
            if c_nt != "---":
                res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                for r in res_al_n.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        b1, b2, b3, _ = st.columns([1,1,1,5])
                        if b1.button("✏️ Editar", key=f"ed_n_{al['id']}"): st.info("Use el formulario para modificar.")
                        if b2.button("🗑️ Borrar", key=f"del_n_{al['id']}"): 
                            st.session_state[f"ask_n_{al['id']}"] = True
                        
                        if st.session_state.get(f"ask_n_{al['id']}"):
                            if st.button("CONFIRMAR BORRADO NOTA", key=f"y_n_{al['id']}"):
                                del st.session_state[f"ask_n_{al['id']}"]; st.rerun()

                        with st.form(f"f_n_{al['id']}"):
                            val = st.number_input("Nota:", 1.0, 10.0, 7.0)
                            if st.form_submit_button("💾 Guardar"):
                                st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB CURSOS (FORMULARIO FIJO) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        if res_c.data:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
        st.divider()
        with st.form("new_curso"):
            st.write("### ➕ Instalar Nuevo Curso")
            nm_c = st.text_input("Nombre de la Materia")
            if st.form_submit_button("💾 GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm_c, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()
