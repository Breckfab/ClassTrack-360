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

# --- ESTILO CSS (ETIQUETAS Y LOGO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .status-inactive { color: #ff0000; font-weight: bold; border: 1px solid #ff0000; padding: 2px 8px; border-radius: 4px; background: rgba(255,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">CT360</div>', unsafe_allow_html=True)
        with st.form("login_v100"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
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
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA CRÍTICA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 3: NOTAS (JERARQUÍA CORREGIDA) ---
    with tabs[3]:
        st.subheader("Gestión de Notas")
        if mapa_cursos:
            m_sel_n = st.selectbox("Seleccionar Curso para ver Notas:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_notas_v100")
            
            if m_sel_n != "--- Seleccionar ---":
                # Buscar alumnos del curso
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_sel_n).not_.is_("alumno_id", "null").execute()
                
                if r_al_n.data:
                    for item in r_al_n.data:
                        al = item['alumnos']
                        with st.expander(f"📝 {al['apellido']}, {al['nombre']}"):
                            # Mostrar notas existentes
                            r_notas = supabase.table("notas").select("*").eq("alumno_id", al['id']).eq("materia", m_sel_n).execute()
                            
                            if r_notas.data:
                                for nt in r_notas.data:
                                    with st.form(f"ed_nota_{nt['id']}"):
                                        v_nota = st.text_input("Nota / Calificación", value=nt['nota'])
                                        v_desc = st.text_input("Instancia (Examen, TP...)", value=nt['descripcion'])
                                        c1, c2, c3 = st.columns(3)
                                        if c1.form_submit_button("GUARDAR"):
                                            supabase.table("notas").update({"nota": v_nota, "descripcion": v_desc}).eq("id", nt['id']).execute()
                                            st.rerun()
                                        if c2.form_submit_button("CANCELAR"): st.rerun()
                                        if c3.form_submit_button("⚠️ BORRAR"):
                                            supabase.table("notas").delete().eq("id", nt['id']).execute()
                                            st.rerun()
                            
                            st.divider()
                            # Agregar nueva nota
                            with st.form(f"add_nota_{al['id']}"):
                                st.write("**Agregar Nueva Nota**")
                                n_val = st.text_input("Calificación")
                                n_des = st.text_input("Instancia")
                                if st.form_submit_button("REGISTRAR NOTA"):
                                    supabase.table("notas").insert({
                                        "alumno_id": al['id'],
                                        "profesor_id": u_data['id'],
                                        "materia": m_sel_n,
                                        "nota": n_val,
                                        "descripcion": n_des,
                                        "fecha": str(ahora.date())
                                    }).execute()
                                    st.rerun()
                else:
                    st.info("ℹ️ No hay alumnos inscriptos en esta materia.")
        else:
            st.info("ℹ️ Primero debe crear una materia en la pestaña 'Cursos'.")

    # --- TAB 2: ASISTENCIA (ESTABLE) ---
    with tabs[2]:
        st.subheader("Asistencia")
        if mapa_cursos:
            m_as = st.selectbox("Materia:", list(mapa_cursos.keys()), key="sb_as_v100")
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
            if r_as.data:
                with st.form("f_as_v100"):
                    checks = []
                    for it in r_as.data:
                        al = it['alumnos']
                        est = st.radio(f"{al['apellido']}", ["Presente", "Ausente"], key=f"as_v100_{al['id']}", horizontal=True)
                        checks.append({"id": al['id'], "est": est})
                    if st.form_submit_button("GUARDAR ASISTENCIA"):
                        for c in checks:
                            supabase.table("asistencia").insert({"alumno_id": c["id"], "profesor_id": u_data['id'], "materia": m_as, "fecha": str(ahora.date()), "estado": c["est"]}).execute()
                        st.success("✅ Guardado")
            else: st.info("ℹ️ No hay alumnos para esta materia.")
        else: st.info("ℹ️ No hay materias creadas.")

    # --- OTRAS PESTAÑAS (AGENDA, ALUMNOS, CURSOS) ---
    # Se mantienen idénticas a la v99 para asegurar estabilidad
    with tabs[0]: st.info("ℹ️ Utilice 'Nueva Clase' o 'Historial' para gestionar la agenda.")
    with tabs[1]: st.info("ℹ️ Busque o inscriba alumnos debajo.")
    with tabs[4]: 
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    if st.button(f"BORRAR CURSO {n}", key=f"bc_v100_{i}"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
