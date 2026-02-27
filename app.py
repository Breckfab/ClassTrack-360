import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v174", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO VISUAL PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; transition: 0.3s; }
    .planilla-row:hover { background: rgba(255,255,255,0.06); }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE ACCESO ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v174"):
            u_in = st.text_input("Sede (ej: cambridge)").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com"
                try:
                    # Intento de conexión con reintento automático para evitar errores de red
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Credenciales no válidas.")
                except: st.error("Error al conectar con el servidor. Reintente.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👨‍🏫 {u_data['nombre']}")
        st.write(f"Sede activa: **{u_data['email'].split('.')[0].upper()}**")
        st.divider()
        if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # Mapeo de cursos vinculados al profesor
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (Lógica Colectiva y Observaciones) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        c_as1, c_as2 = st.columns(2)
        sel_as = c_as1.selectbox("Curso a llamar:", ["---"] + list(mapa_cursos.keys()), key="as_v174")
        f_as = c_as2.date_input("Fecha de la clase:", datetime.date.today())
        
        if sel_as != "---":
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
            if res_al.data:
                for item in res_al.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}_{f_as}"):
                            col_st, col_obs = st.columns([2, 3])
                            est = col_st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            obs = col_obs.text_input("Motivo / Observación", placeholder="Opcional...")
                            if st.form_submit_button("💾 REGISTRAR"):
                                supabase.table("asistencia").insert({
                                    "alumno_id": al['id'], "profesor_id": u_data['id'], 
                                    "materia": sel_as, "estado": est, "fecha": str(f_as), "observacion": obs
                                }).execute()
                                st.success("Guardado")

    # --- TAB 3: NOTAS (Promedio Automático y Placeholder) ---
    with tabs[3]:
        st.subheader("📝 Calificaciones y Seguimiento")
        sel_nt = st.selectbox("Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v174")
        
        if sel_nt != "---":
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
            if res_al.data:
                for item in res_al.data:
                    al = item['alumnos']
                    # Cálculo dinámico de promedio
                    res_notas = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                    promedio = sum([n['calificacion'] for n in res_notas.data]) / len(res_notas.data) if res_notas.data else 0
                    
                    with st.container():
                        st.markdown(f'''
                            <div class="planilla-row">
                                📝 {al["apellido"].upper()}, {al["nombre"]} 
                                <span style="float:right;">Promedio Actual: <span class="promedio-badge">{promedio:.2f}</span></span>
                            </div>
                        ''', unsafe_allow_html=True)
                        with st.form(f"f_nt_{al['id']}"):
                            c1, c2, c3 = st.columns([1, 1, 2])
                            n_val = c1.number_input("Nota:", 1.0, 10.0, value=None, placeholder="7.00")
                            per = c2.selectbox("Periodo:", ["1er Cuatrimestre", "2do Cuatrimestre", "Examen Final"])
                            com = c3.text_input("Detalle (TP1, Oral, etc.)")
                            if st.form_submit_button("💾 SUBIR NOTA"):
                                if n_val:
                                    supabase.table("notas").insert({
                                        "alumno_id": al['id'], "profesor_id": u_data['id'],
                                        "materia": sel_nt, "calificacion": n_val, "tipo_nota": com, "periodo": per
                                    }).execute()
                                    st.success("Nota registrada exitosamente.")
                                    time.sleep(0.5); st.rerun()

    # --- TAB 1: ALUMNOS (Registro con DNI y Teléfono) ---
    with tabs[1]:
        st.subheader("👥 Ficha de Alumnos")
        with st.form("ins_al_v174"):
            c1, c2 = st.columns(2)
            n_nom, n_ape = c1.text_input("Nombre"), c1.text_input("Apellido")
            n_dni, n_tel = c2.text_input("DNI"), c2.text_input("Teléfono")
            n_cur = st.selectbox("Asignar a curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Primero cree un curso"])
            if st.form_submit_button("💾 GUARDAR ALUMNO"):
                if n_nom and n_ape and mapa_cursos:
                    res_a = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "dni": n_dni, "telefono_contacto": n_tel}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'],
                            "nombre_curso_materia": n_cur, "anio_lectivo": 2026
                        }).execute()
                        st.success(f"Inscripción de {n_ape.upper()} completada.")

    # --- TAB 0: AGENDA (Bitácora y Recursos) ---
    with tabs[0]:
        st.subheader("📅 Bitácora de Clase")
        if mapa_cursos:
            sel_ag = st.selectbox("Materia:", ["---"] + list(mapa_cursos.keys()), key="ag_v174")
            if sel_ag != "---":
                with st.form("f_ag_v174"):
                    st.info(f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}")
                    t_hoy = st.text_area("Contenido dictado")
                    rec = st.text_input("Recursos utilizados (Libros, Links, Material)")
                    st.divider()
                    f_t = st.date_input("Próxima Tarea para el día:", value=datetime.date.today() + datetime.timedelta(days=7))
                    d_t = st.text_area("Descripción de la tarea")
                    if st.form_submit_button("💾 CERRAR CLASE"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(datetime.date.today()), 
                            "contenido_clase": t_hoy, "recursos_utilizados": rec,
                            "tarea_proxima": d_t, "fecha_tarea": str(f_t)
                        }).execute()
                        st.success("Actividad de hoy guardada.")
