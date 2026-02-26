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

# --- ESTILO CSS Y RELOJ DISCRETO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 15px; }
    .clock-discreet { 
        font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #ffffff; 
        text-align: center; padding: 5px; margin-bottom: 20px; font-weight: 400;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    
    <div class="clock-discreet" id="live-clock">Cargando hora...</div>

    <script>
    function startTime() {
        const today = new Date();
        let h = today.getHours();
        let m = today.getMinutes();
        let s = today.getSeconds();
        m = m < 10 ? "0" + m : m;
        s = s < 10 ? "0" + s : s;
        document.getElementById('live-clock').innerHTML = h + ":" + m + ":" + s;
        setTimeout(startTime, 1000);
    }
    startTime();
    </script>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v110"):
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

    # --- CARGA MAESTRA DE DATOS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if mapa_cursos:
            m_age = st.selectbox("Elegir Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="sb_age_v110")
            if m_age != "--- Seleccionar ---":
                with st.form("f_age_v110"):
                    t1 = st.text_area("Temas dictados")
                    st.write("📅 **Programar Tarea**")
                    f_tar = st.date_input("Fecha de entrega", value=datetime.date.today())
                    t2 = st.text_area("Detalle de la tarea")
                    if st.form_submit_button("GUARDAR REGISTRO"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_age], 
                            "fecha": str(datetime.date.today()), 
                            "contenido_clase": t1, 
                            "tarea_proxima": t2,
                            "fecha_tarea": str(f_tar)
                        }).execute()
                        st.success("✅ Guardado correctamente")
                        st.rerun()
        else: st.info("ℹ️ No hay materias creadas actualmente.")

    # --- TAB 1: ALUMNOS (ETIQUETAS Y BORRADO) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        # Listado existente primero
        try:
            r_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, estado), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for item in r_al.data:
                    alu = item['alumnos']
                    if alu:
                        with st.expander(f"👤 {alu['apellido']}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                            with st.form(f"ed_al_v110_{alu['id']}"):
                                n_n = st.text_input("Nombre", value=alu['nombre'])
                                n_a = st.text_input("Apellido", value=alu['apellido'])
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("ACTUALIZAR"):
                                    supabase.table("alumnos").update({"nombre": n_n, "apellido": n_a}).eq("id", alu['id']).execute()
                                    st.rerun()
                                if c2.form_submit_button("CANCELAR"): st.rerun()
                                if c3.form_submit_button("⚠️ BORRAR"):
                                    supabase.table("alumnos").delete().eq("id", alu['id']).execute()
                                    st.rerun()
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: pass

        st.divider()
        with st.expander("➕ Inscribir Alumno Nuevo"):
            if mapa_cursos:
                with st.form("f_ins_v110"):
                    m_ins = st.selectbox("Materia:", list(mapa_cursos.keys()))
                    n_ins, a_ins = st.text_input("Nombre"), st.text_input("Apellido")
                    if st.form_submit_button("GUARDAR ALUMNO"):
                        res_a = supabase.table("alumnos").insert({"nombre": n_ins, "apellido": a_ins, "estado": "ACTIVO"}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": m_ins, "anio_lectivo": 2026}).execute()
                            st.rerun()

    # --- TAB 4: CURSOS (LÓGICA INVERTIDA Y TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("Mis Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_cur_v110_{i}"):
                        new_name = st.text_input("Nombre de la Materia", value=n)
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_name}).eq("id", i).execute()
                            st.rerun()
                        if bc2.form_submit_button("CANCELAR"): st.rerun()
                        if bc3.form_submit_button("⚠️ BORRAR DEFINITIVO"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        st.divider()
        with st.form("f_new_c_v110"):
            nc = st.text_input("Nueva Materia")
            if st.form_submit_button("AGREGAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
