import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v176", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v176"):
            u_in = st.text_input("Sede (ej: cambridge)").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
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
        st.write(f"Sede: **{u_data['email'].split('.')[0].upper()}**")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # MAPEO DE CURSOS (Para que todo el sistema reconozca las materias creadas)
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (FIXED: AHORA ACTUALIZA AL INSTANTE) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Materias")
        with st.form("new_cur_v176"):
            c_nom = st.text_input("Nombre de la nueva Materia / Curso (Ej: Inglés 1)")
            if st.form_submit_button("💾 CREAR E INSTALAR CURSO"):
                if c_nom:
                    try:
                        supabase.table("inscripciones").insert({
                            "profesor_id": u_data['id'], 
                            "nombre_curso_materia": c_nom, 
                            "anio_lectivo": 2026
                        }).execute()
                        st.success(f"Curso '{c_nom}' creado satisfactoriamente.")
                        time.sleep(1)
                        st.rerun() # Disparador de refresco
                    except:
                        st.error("Error al crear. Revise la conexión.")

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("📅 Bitácora de Clase")
        if not mapa_cursos:
            st.warning("⚠️ Primero cree una materia en la pestaña 'Cursos'.")
        else:
            sel_ag = st.selectbox("Materia:", ["---"] + list(mapa_cursos.keys()), key="ag_v176")
            if sel_ag != "---":
                with st.form("f_ag_v176"):
                    t_hoy = st.text_area("Contenido dictado")
                    rec = st.text_input("Recursos utilizados")
                    st.divider()
                    f_t = st.date_input("Próxima Tarea:", value=datetime.date.today() + datetime.timedelta(days=7))
                    d_t = st.text_area("Descripción de la tarea")
                    if st.form_submit_button("💾 GUARDAR ACTIVIDAD"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(datetime.date.today()), 
                            "contenido_clase": t_hoy, "recursos_utilizados": rec,
                            "tarea_proxima": d_t, "fecha_tarea": str(f_t)
                        }).execute()
                        st.success("Guardado.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        with st.form("ins_al_v176"):
            c1, c2 = st.columns(2)
            n_nom, n_ape = c1.text_input("Nombre"), c1.text_input("Apellido")
            n_dni, n_tel = c2.text_input("DNI"), c2.text_input("Teléfono")
            n_cur = st.selectbox("Asignar a curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
            if st.form_submit_button("💾 GUARDAR ALUMNO"):
                if n_nom and n_ape and mapa_cursos:
                    res_a = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "dni": n_dni, "telefono_contacto": n_tel}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'],
                            "nombre_curso_materia": n_cur, "anio_lectivo": 2026
                        }).execute()
                        st.success(f"Alumno {n_ape.upper()} registrado.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            c_as1, c_as2 = st.columns(2)
            sel_as = c_as1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v176")
            f_as = c_as2.date_input("Fecha:", datetime.date.today())
            if sel_as != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
                for item in res_al.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}_{f_as}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_as, "estado": est, "fecha": str(f_as)}).execute()
                                st.success("Ok")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("📝 Notas")
        if mapa_cursos:
            sel_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v176")
            if sel_nt != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
                for item in res_al.data:
                    al = item['alumnos']
                    res_n = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                    prom = sum([n['calificacion'] for n in res_n.data]) / len(res_n.data) if res_n.data else 0
                    with st.container():
                        st.markdown(f'<div class="planilla-row">📝 {al["apellido"].upper()}, {al["nombre"]} <span style="float:right;">Promedio: <span class="promedio-badge">{prom:.2f}</span></span></div>', unsafe_allow_html=True)
                        with st.form(f"f_nt_{al['id']}"):
                            n_val = st.number_input("Nota:", 1.0, 10.0, value=None, placeholder="7.00")
                            if st.form_submit_button("💾 GRABAR NOTA"):
                                if n_val:
                                    supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_nt, "calificacion": n_val}).execute()
                                    st.success("Nota grabada"); time.sleep(0.5); st.rerun()
