import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v206", layout="wide")

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

    # --- DATOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB NOTAS (CASCADA SIN BLOQUEO) ---
    with tabs[3]:
        st.subheader("📝 Notas por Curso")
        if not mapa_cursos: st.info("Cree un curso primero.")
        else:
            c_nt = st.selectbox("Seleccione el curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
            if c_nt != "---":
                res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                for r in res_al_n.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_n_{al['id']}"):
                            nota = st.number_input("Nota (7.00):", 1.0, 10.0, 7.0, 0.1)
                            obs = st.text_input("Comentario")
                            b1, b2, b3, _ = st.columns([1,1,1,5])
                            # Triple botonera
                            if b3.form_submit_button("💾 Guardar"):
                                supabase.table("notas").insert({"alumno_id":al['id'], "profesor_id":u_data['id'], "materia":c_nt, "calificacion":nota, "comentario":obs, "fecha":str(datetime.date.today())}).execute()
                                st.success("Cambios guardados satisfactoriamente.")
                                time.sleep(1); st.rerun()

    # --- TAB ASISTENCIA (CASCADA SIN BLOQUEO) ---
    with tabs[2]:
        st.subheader("✅ Asistencia por Curso")
        if not mapa_cursos: st.info("Cree un curso primero.")
        else:
            c_as = st.selectbox("Seleccione el curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel")
            if c_as != "---":
                res_al_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_al_as.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 Guardar"):
                                supabase.table("asistencia").insert({"alumno_id":al['id'], "profesor_id":u_data['id'], "materia":c_as, "estado":est, "fecha":str(datetime.date.today())}).execute()
                                st.success("Cambios guardados satisfactoriamente.")
                                time.sleep(1); st.rerun()

    # --- TAB CURSOS (LISTADO ARRIBA CON LIMPIEZA) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos Existentes")
        for c in res_c.data:
            with st.container():
                st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                if cb2.button("🗑️ Borrar", key=f"d_c_{c['id']}"):
                    st.session_state[f"ask_c_{c['id']}"] = True
                
                if st.session_state.get(f"ask_c_{c['id']}"):
                    st.warning("¿Confirmar eliminación?")
                    if st.button("SÍ, ELIMINAR", key=f"y_c_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                        del st.session_state[f"ask_c_{c['id']}"] # LIMPIEZA
                        st.rerun()

    # --- TAB ALUMNOS (TRIPLE BOTONERA Y LIMPIEZA) ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        # Lógica de inscripción y listado con st.rerun() tras borrar
