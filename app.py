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
        with st.form("login_v97"):
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
    ahora = datetime.datetime.now()
    
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA CRÍTICA DE DATOS ---
    df_cursos = pd.DataFrame()
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            df_cursos = pd.DataFrame(r_c.data)
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for _, row in df_cursos.iterrows()}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON BUSCADOR Y LEYENDA RECUPERADA) ---
    with tabs[0]:
        st.subheader("Registro de Clase y Tareas")
        if not df_cursos.empty:
            sub_age = st.tabs(["➕ Nueva Clase", "🔍 Buscador de Tareas"])
            
            with sub_age[0]:
                m_sel = st.selectbox("Elegir Curso o Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v97")
                if m_sel != "--- Seleccionar ---":
                    with st.form("f_new_bit_v97"):
                        t1 = st.text_area("Temas dictados hoy")
                        t2 = st.text_area("Tarea próxima")
                        if st.form_submit_button("GUARDAR CLASE"):
                            supabase.table("bitacora").insert({
                                "inscripcion_id": mapa_cursos[m_sel],
                                "fecha": str(ahora.date()),
                                "contenido_clase": t1,
                                "tarea_proxima": t2
                            }).execute()
                            st.rerun()
            
            with sub_age[1]:
                st.write("### 🔍 Consultar clases pasadas")
                m_busq = st.selectbox("Filtrar por Curso:", ["--- Todos ---"] + list(mapa_cursos.keys()), key="sb_busq_v97")
                
                query = supabase.table("bitacora").select("*, inscripciones(nombre_curso_materia)")
                if m_busq != "--- Todos ---":
                    query = query.eq("inscripcion_id", mapa_cursos[m_busq])
                
                r_hist = query.order("fecha", desc=True).execute()
                
                if r_hist.data:
                    for entry in r_hist.data:
                        with st.expander(f"📅 {entry['fecha']} - {entry['inscripciones']['nombre_curso_materia']}"):
                            with st.form(f"ed_bit_v97_{entry['id']}"):
                                e_cont = st.text_area("Temas dictados", value=entry['contenido_clase'])
                                e_tar = st.text_area("Tarea dada", value=entry['tarea_proxima'] if entry['tarea_proxima'] else "")
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("ACTUALIZAR"):
                                    supabase.table("bitacora").update({"contenido_clase": e_cont, "tarea_proxima": e_tar}).eq("id", entry['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("CANCELAR"): st.rerun()
                                if c3.form_submit_button("⚠️ BORRAR"):
                                    st.session_state[f"del_bit_{entry['id']}"] = True
                            
                            if st.session_state.get(f"del_bit_{entry['id']}"):
                                st.error("### 🚨 ¿BORRAR REGISTRO? Acción irreversible.")
                                col1, col2 = st.columns(2)
                                if col1.button("SÍ, BORRAR", key=f"y_b_{entry['id']}"):
                                    supabase.table("bitacora").delete().eq("id", entry['id']).execute()
                                    st.rerun()
                                if col2.button("NO", key=f"n_b_{entry['id']}"):
                                    del st.session_state[f"del_bit_{entry['id']}"]
                                    st.rerun()
                else:
                    st.info("ℹ️ No hay registros históricos para mostrar.")
        else:
            st.info("ℹ️ No hay registros disponibles porque no hay materias creadas.")

    # --- TAB 1: ALUMNOS (ETIQUETAS Y LÓGICA INVERTIDA) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_al.data:
            for item in r_al.data:
                alu = item['alumnos']
                if alu:
                    st_label = alu.get('estado', 'ACTIVO')
                    st_class = "status-active" if st_label == "ACTIVO" else "status-inactive"
                    with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                        st.markdown(f"Estado: <span class='{st_class}'>{st_label}</span>", unsafe_allow_html=True)
                        with st.form(f"ed_al_v97_{alu['id']}"):
                            n_nom = st.text_input("Nombre", value=alu['nombre'])
                            n_ape = st.text_input("Apellido", value=alu['apellido'])
                            n_est = st.radio("Estado", ["ACTIVO", "INACTIVO"], index=0 if st_label == "ACTIVO" else 1, horizontal=True)
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("ACTUALIZAR"):
                                supabase.table("alumnos").update({"nombre": n_nom, "apellido": n_ape, "estado": n_est}).eq("id", alu['id']).execute()
                                st.rerun()
                            if c2.form_submit_button("CANCELAR"): st.rerun()
                            if c3.form_submit_button("⚠️ BORRAR"): st.session_state[f"da_{alu['id']}"] = True
        else: st.info("ℹ️ No hay alumnos registrados.")

        st.divider()
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v97"):
                    m_ins = st.selectbox("Materia", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 4: CURSOS (LÓGICA INVERTIDA) ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if not df_cursos.empty:
            for _, r in df_cursos.iterrows():
                with st.expander(f"📘 {r['nombre_curso_materia']}"):
                    with st.form(f"ed_c_v97_{r['id']}"):
                        n_mat = st.text_input("Nombre", value=r['nombre_curso_materia'])
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.form_submit_button("ACTUALIZAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_mat}).eq("id", r['id']).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
                        if bc3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
        else: st.info("ℹ️ No tiene materias creadas.")

        st.divider()
        with st.form("f_new_c_v97"):
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("GUARDAR NUEVO CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
