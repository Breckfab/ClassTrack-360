import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v180", layout="wide")

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
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    #reloj-fijo { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #4facfe; z-index: 10000; background: rgba(0,0,0,0.5); padding: 5px 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DEL RELOJ (HTML/JS) ---
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

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v180"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com"
                try:
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado.")
                except: st.error("Error de conexión.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👨‍🏫 {u_data['nombre']}")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # MAPEO DE CURSOS (Vital para que Agenda y Alumnos no estén en negro)
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (ACTIVA) ---
    with tabs[0]:
        st.subheader("📅 Bitácora de Clase")
        if not mapa_cursos:
            st.info("💡 Primero cree una materia en la pestaña 'Cursos'.")
        else:
            sel_ag = st.selectbox("Seleccionar Materia:", ["---"] + list(mapa_cursos.keys()), key="ag_v180")
            if sel_ag != "---":
                with st.form("f_ag_v180"):
                    t_hoy = st.text_area("Temas dictados hoy")
                    rec = st.text_input("Recursos utilizados")
                    f_t = st.date_input("Próxima tarea:", value=datetime.date.today() + datetime.timedelta(days=7))
                    d_t = st.text_area("Descripción de tarea")
                    if st.form_submit_button("💾 GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(datetime.date.today()), 
                            "contenido_clase": t_hoy, "recursos_utilizados": rec,
                            "tarea_proxima": d_t, "fecha_tarea": str(f_t)
                        }).execute()
                        st.success("Actividad guardada correctamente.")

    # --- TAB 1: ALUMNOS (ACTIVA) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.form("ins_al_v180"):
            c1, c2 = st.columns(2)
            n_nom, n_ape = c1.text_input("Nombre"), c1.text_input("Apellido")
            n_dni, n_tel = c2.text_input("DNI"), c2.text_input("Teléfono")
            n_cur = st.selectbox("Asignar a curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
            if st.form_submit_button("💾 REGISTRAR ALUMNO"):
                if n_nom and n_ape and mapa_cursos:
                    res_a = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "dni": n_dni, "telefono_contacto": n_tel}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": n_cur, "anio_lectivo": 2026}).execute()
                        st.success(f"✅ {n_ape.upper()} registrado satisfactoriamente.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            c_as1, c_as2 = st.columns(2)
            sel_as = c_as1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v180")
            f_as = c_as2.date_input("Fecha:", datetime.date.today())
            if sel_as != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
                for it in res_al.data:
                    al = it['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{al['id']}_{f_as}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True, key=f"r_{al['id']}")
                            if st.form_submit_button("💾 GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_as, "estado": est, "fecha": str(f_as)}).execute()
                                st.success("Ok")

    # --- TAB 3: NOTAS (FIX PROMEDIO) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            sel_nt = st.selectbox("Materia:", ["---"] + list(mapa_cursos.keys()), key="nt_v180")
            if sel_nt != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
                for it in res_al.data:
                    al = it['alumnos']
                    res_n = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                    prom = 0.0
                    if res_n.data:
                        vals = [float(n['calificacion']) for n in res_n.data]
                        prom = sum(vals) / len(vals)
                    with st.container():
                        st.markdown(f'<div class="planilla-row">📝 {al["apellido"].upper()}, {al["nombre"]} <span style="float:right;">Promedio: <span class="promedio-badge">{prom:.2f}</span></span></div>', unsafe_allow_html=True)
                        with st.form(f"nt_{al['id']}"):
                            n_v = st.number_input("Nota:", 1.0, 10.0, value=None, placeholder="7.00")
                            if st.form_submit_button("💾 GRABAR NOTA"):
                                if n_v:
                                    supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_nt, "calificacion": float(n_v)}).execute()
                                    st.success("Grabado"); time.sleep(0.5); st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("new_cur_v180"):
            c_nom = st.text_input("Nombre de la Materia")
            if st.form_submit_button("💾 CREAR CURSO"):
                if c_nom:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": c_nom, "anio_lectivo": 2026}).execute()
                    st.success("Curso creado"); time.sleep(1); st.rerun()
