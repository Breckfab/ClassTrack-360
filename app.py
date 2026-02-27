import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v173", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border-top: 1px solid rgba(255,255,255,0.1); }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN REFORZADO ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v173"):
            u_in = st.text_input("Sede (ej: cambridge)").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com"
                try:
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado. Verifique sede y clave.")
                except: st.error("Error de conexión con la base de datos.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 📍 {u_data['nombre']}")
        st.write(f"Sede: {u_data['email'].split('.')[0].upper()}")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # Cargar cursos del profesor
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (PLANILLA COLECTIVA) ---
    with tabs[2]:
        st.subheader("✅ Asistencia Colectiva")
        col_as1, col_as2 = st.columns(2)
        sel_as = col_as1.selectbox("Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel")
        f_as = col_as2.date_input("Fecha de clase:", datetime.date.today())
        
        if sel_as != "---":
            # Traer alumnos inscriptos en este curso
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
            if res_al.data:
                for item in res_al.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"f_as_{al['id']}_{f_as}"):
                            col_st, col_obs = st.columns([2, 3])
                            est = col_st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True, key=f"radio_{al['id']}")
                            obs = col_obs.text_input("Observación / Justificación", placeholder="Ej: Médico, Entró tarde...")
                            if st.form_submit_button("💾 GUARDAR ASISTENCIA"):
                                supabase.table("asistencia").insert({
                                    "alumno_id": al['id'], "profesor_id": u_data['id'], 
                                    "materia": sel_as, "estado": est, "fecha": str(f_as), "observacion": obs
                                }).execute()
                                st.success(f"Grabado: {al['apellido']}")

    # --- TAB 3: NOTAS (PLANILLA COLECTIVA + PROMEDIO) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Calificaciones")
        sel_nt = st.selectbox("Llamar Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
        
        if sel_nt != "---":
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
            if res_al.data:
                for item in res_al.data:
                    al = item['alumnos']
                    
                    # Cálculo de promedio automático
                    res_notas = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                    promedio = sum([n['calificacion'] for n in res_notas.data]) / len(res_notas.data) if res_notas.data else 0
                    
                    with st.container():
                        st.markdown(f'''
                            <div class="planilla-row">
                                📝 {al["apellido"].upper()}, {al["nombre"]} 
                                <span style="float:right;">Promedio: <span class="promedio-badge">{promedio:.2f}</span></span>
                            </div>
                        ''', unsafe_allow_html=True)
                        with st.form(f"f_nt_{al['id']}"):
                            c1, c2, c3 = st.columns([1, 1, 2])
                            n_val = c1.number_input("Nota:", 1.0, 10.0, value=None, placeholder="Ej: 8.5")
                            per = c2.selectbox("Periodo:", ["1er Cuatrimestre", "2do Cuatrimestre", "Final"])
                            com = c3.text_input("Instancia (Ej: TP1, Examen...)")
                            if st.form_submit_button("💾 GRABAR NOTA"):
                                if n_val:
                                    supabase.table("notas").insert({
                                        "alumno_id": al['id'], "profesor_id": u_data['id'],
                                        "materia": sel_nt, "calificacion": n_val, "tipo_nota": com, "periodo": per
                                    }).execute()
                                    st.success("Nota guardada")
                                    time.sleep(0.5); st.rerun()

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        with st.form("ins_al_v173"):
            col1, col2 = st.columns(2)
            n_nom = col1.text_input("Nombre")
            n_ape = col1.text_input("Apellido")
            n_dni = col2.text_input("DNI")
            n_tel = col2.text_input("Teléfono")
            n_cur = st.selectbox("Inscribir en curso:", list(mapa_cursos.keys()))
            if st.form_submit_button("💾 REGISTRAR E INSCRIBIR"):
                if n_nom and n_ape:
                    res_a = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "dni": n_dni, "telefono_contacto": n_tel}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'],
                            "nombre_curso_materia": n_cur, "anio_lectivo": 2026
                        }).execute()
                        st.success(f"✅ {n_ape} inscripto satisfactoriamente.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("new_cur"):
            c_nom = st.text_input("Nombre de la Materia / Curso")
            if st.form_submit_button("💾 CREAR CURSO"):
                if c_nom:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": c_nom, "anio_lectivo": 2026}).execute()
                    st.success(f"Curso {c_nom} creado.")
                    st.rerun()
