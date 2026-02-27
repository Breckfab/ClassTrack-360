import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v204", layout="wide")

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

    # --- TAB AGENDA (BITÁCORA Y TAREAS) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data: st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA HOY: {res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            with st.form("f_ag"):
                temas = st.text_area("Temas dictados")
                tarea = st.text_area("Tarea para la próxima")
                vto = st.date_input("Vence el:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Satisactorio.")

    # --- TAB ALUMNOS (CARGA Y LISTA POR CURSO) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            with st.form("new_al"):
                nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                dn = st.text_input("DNI")
                c_sel = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    res_a = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape, "dni": dn}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                        st.success("Satisfactorio."); st.rerun()
        
        c_list = st.selectbox("Filtrar lista por curso:", ["Todos"] + list(mapa_cursos.keys()))
        res_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null")
        if c_list != "Todos": res_al = res_al.eq("nombre_curso_materia", c_list)
        res_al = res_al.execute()
        for r in res_al.data:
            with st.container():
                st.markdown(f'<div class="planilla-row">👤 {r["alumnos"]["apellido"].upper()}, {r["alumnos"]["nombre"]} ({r["nombre_curso_materia"]})</div>', unsafe_allow_html=True)
                if st.button("🗑️ Borrar", key=f"del_{r['id']}"):
                    supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                    st.rerun()

    # --- TAB ASISTENCIA (POR CURSO) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            c_as = st.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="as_c")
            if c_as != "---":
                res_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for item in res_as.data:
                    al = item['alumnos']
                    with st.form(f"as_{al['id']}"):
                        st.write(f"👤 {al['apellido'].upper()}, {al['nombre']}")
                        est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                        if st.form_submit_button("💾"):
                            supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                            st.success("Ok")

    # --- TAB NOTAS (POR CURSO) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            c_nt = st.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_c")
            if c_nt != "---":
                res_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                for item in res_nt.data:
                    al = item['alumnos']
                    with st.form(f"nt_{al['id']}"):
                        st.write(f"👤 {al['apellido'].upper()}, {al['nombre']}")
                        n = st.number_input("Nota:", 1.0, 10.0, value=7.0, step=0.1)
                        com = st.text_input("Comentario")
                        if st.form_submit_button("💾"):
                            supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_nt, "calificacion": n, "comentario": com, "fecha": str(datetime.date.today())}).execute()
                            st.success("Ok")

    # --- TAB CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("new_c"):
            nm = st.text_input("Materia")
            hr = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{nm} ({hr})", "anio_lectivo": 2026}).execute()
                st.rerun()
