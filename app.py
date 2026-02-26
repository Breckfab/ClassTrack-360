import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v143", layout="wide")

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
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ ---
components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; z-index:9999;">--:--:--</div>
    <script>
    function t(){
        const n=new Date();
        const h=String(n.getHours()).padStart(2,'0');
        const m=String(n.getMinutes()).padStart(2,'0');
        const s=String(n.getSeconds()).padStart(2,'0');
        document.getElementById('rtc').innerText=h+":"+m+":"+s;
    }
    setInterval(t,1000); t();
    </script>
    """, height=40)

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v143"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                    if res and res.data:
                        st.session_state.user = res.data[0]
                        st.rerun()
                    else: st.error("Acceso denegado.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"Sede: {u_data['email'].split('.')[0].capitalize()}")
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA DE CURSOS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (SELECTOR CORREGIDO) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clases")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        sel_ag_c = st.selectbox("📍 Seleccionar Curso para Agenda:", ["---"] + list(mapa_cursos.keys()), key="v143_ag_c")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if sel_ag_c != "---":
            with st.form("f_ag_v143"):
                temas = st.text_area("Temas dictados hoy")
                f_t = st.date_input("Fecha próxima tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                d_t = st.text_area("Descripción de la tarea")
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag_c], "fecha": str(datetime.date.today()), "contenido_clase": temas, "tarea_proxima": d_t, "fecha_tarea": str(f_t)}).execute()
                    st.success("Agenda guardada.")

    # --- TAB 3: NOTAS (RESTAURADO CON BUSCADORES) ---
    with tabs[3]:
        st.subheader("📝 Gestión de Notas")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        nc1, nc2 = st.columns(2)
        f_nt_cur = nc1.selectbox("📍 Filtrar por Curso:", ["---"] + list(mapa_cursos.keys()), key="v143_nt_c")
        f_nt_bus = nc2.text_input("🔍 Buscar Alumno (Apellido):", key="v143_nt_b").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        if f_nt_cur != "---":
            try:
                r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_cur).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_nt_bus in al['apellido'].lower():
                            with st.expander(f"📝 CALIFICAR: {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_nota_{al['id']}"):
                                    v_nota = st.number_input("Calificación (1-10)", 1, 10, 7)
                                    v_tipo = st.selectbox("Instancia:", ["Examen", "TP", "Concepto", "Final"])
                                    if st.form_submit_button("💾 GRABAR NOTA"):
                                        supabase.table("notas").insert({"alumno_id": al['id'], "materia": f_nt_cur, "calificacion": v_nota, "tipo_nota": v_tipo, "fecha": str(datetime.date.today())}).execute()
                                        st.success("Nota registrada con éxito.")
                else: st.warning("No hay alumnos inscriptos en este curso.")
            except: st.error("Error al cargar alumnos.")

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN Y BUSCADORES) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        f_al_c = ac1.selectbox("📍 Filtrar Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v143_al_c")
        f_al_n = ac2.text_input("🔍 Buscar Apellido:", key="v143_al_n").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("ins_al_v143"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Materia:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin materias"])
                if st.form_submit_button("💾 REGISTRAR"):
                    res_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                        st.success("Inscripto."); st.rerun()

    # --- TAB 2: ASISTENCIA (BUSCADORES Y CARGA) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        asc1, asc2 = st.columns(2)
        f_as_c = asc1.selectbox("📍 Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="v143_as_c")
        f_as_n = asc2.text_input("🔍 Buscar Alumno:", key="v143_as_n").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        if f_as_c != "---":
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_as_c).not_.is_("alumno_id", "null").execute()
            for it in r_as.data:
                al = it['alumnos']
                if f_as_n in al['apellido'].lower():
                    with st.expander(f"📌 {al['apellido'].upper()}, {al['nombre']}"):
                        with st.form(f"f_as_{al['id']}"):
                            est = st.radio("Asistencia:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 GRABAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": f_as_c, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Ok.")

    # --- TAB 4: CURSOS (LISTADO COMPLETO) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("new_c_v143"):
            n_c = st.text_input("Nombre de Materia")
            if st.form_submit_button("💾 GRABAR MATERIA"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_c, "anio_lectivo": 2026}).execute()
                st.rerun()
        st.divider()
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"op_c_{i}"):
                        st.text_input("Materia", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("GUARDAR"): st.rerun()
                        if c2.form_submit_button("CANCELAR"): st.rerun()
                        if c3.form_submit_button("BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
