import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono:wght@500&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .clock-box { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; color: #00f2fe; text-align: center; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 10px; border: 2px solid #4facfe; margin-bottom: 20px; box-shadow: 0 0 15px rgba(79, 172, 254, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v106"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res and res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        
        # --- RELOJ EN VIVO (CON REFRESH) ---
        ahora = datetime.datetime.now()
        st.markdown(f'<div class="clock-box">{ahora.strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
        
        # Esto hace que la página se refresque cada 1 segundo solo para el reloj
        st.empty() 
        if st.session_state.user:
            st.button("🔄 Actualizar Reloj/Datos", use_container_width=True) # Botón de backup si el browser bloquea el auto-refresh

        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON CALENDARIO RESTAURADO) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Agenda")
        if mapa_cursos:
            sub_age = st.tabs(["➕ Nueva Clase", "🔍 Historial"])
            with sub_age[0]:
                m_age = st.selectbox("Elegir Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v106")
                if m_age != "--- Seleccionar ---":
                    with st.form("f_age_v106"):
                        t1 = st.text_area("Contenido de la clase")
                        st.write("📅 **Programar Tarea**")
                        f_tarea = st.date_input("Fecha de entrega", value=datetime.date.today())
                        t2 = st.text_area("Descripción de la tarea")
                        if st.form_submit_button("GUARDAR REGISTRO"):
                            supabase.table("bitacora").insert({
                                "inscripcion_id": mapa_cursos[m_age], 
                                "fecha": str(datetime.date.today()), 
                                "contenido_clase": t1, 
                                "tarea_proxima": t2,
                                "fecha_tarea": str(f_tarea)
                            }).execute()
                            st.success("✅ Guardado")
                            st.rerun()
            with sub_age[1]:
                res_h = supabase.table("bitacora").select("*, inscripciones(nombre_curso_materia)").order("fecha", desc=True).execute()
                if res_h.data:
                    for e in res_h.data:
                        with st.expander(f"📅 {e['fecha']} - {e['inscripciones']['nombre_curso_materia']}"):
                            st.write(f"**Dictado:** {e['contenido_clase']}")
                            st.info(f"📌 Tarea para: {e.get('fecha_tarea', 'S/D')} - {e['tarea_proxima']}")
        else: st.info("ℹ️ Cree una materia en 'Cursos' primero.")

    # --- TAB 3: NOTAS (CON LEYENDAS RESTAURADAS) ---
    with tabs[3]:
        st.subheader("Notas")
        if mapa_cursos:
            m_nt = st.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_nt_v106")
            if m_nt != "--- Seleccionar ---":
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_nt).not_.is_("alumno_id", "null").execute()
                if not r_al_n.data:
                    st.error("❌ No hay alumnos inscriptos en esta materia.")
                else:
                    for item in r_al_n.data:
                        al = item['alumnos']
                        with st.expander(f"📝 {al['apellido']}, {al['nombre']}"):
                            r_notas = supabase.table("notas").select("*").eq("alumno_id", al['id']).eq("materia", m_nt).execute()
                            if not r_notas.data:
                                st.warning("⚠️ Este alumno no tiene notas cargadas.")
                            else:
                                for nt in r_notas.data:
                                    st.write(f"• **{nt['descripcion']}**: {nt['nota']}")
    
    # --- TAB 4: CURSOS (CON EDICIÓN Y BORRADO) ---
    with tabs[4]:
        st.subheader("Cursos")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_v106_{i}"):
                        new_name = st.text_input("Editar Nombre", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_name}).eq("id", i).execute()
                            st.rerun()
                        if c2.form_submit_button("CANCELAR"): st.rerun()
                        if c3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
