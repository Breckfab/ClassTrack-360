import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v129", layout="wide")

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
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .st-inactive { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; background: rgba(255,75,75,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ AUTOMÁTICO ---
components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; font-weight:400; z-index:9999;">--:--:--</div>
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
        with st.form("login_v129"):
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
    # --- BARRA LATERAL (RESTABLECIDA) ---
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        st.divider()
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, estado").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: {"id": row['id'], "estado": row.get('estado', 'ACTIVO')} for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RESTABLECIDA CON CALENDARIO Y TAREA) ---
    with tabs[0]:
        st.subheader("📅 Registro de Agenda y Tareas")
        if mapa_cursos:
            m_age = st.selectbox("Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="v129_ag")
            if m_age != "---":
                with st.form("f_agenda_full"):
                    f_hoy = datetime.date.today()
                    st.write(f"Fecha de Clase: {f_hoy.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados hoy")
                    st.divider()
                    st.write("📌 Programar Tarea")
                    f_tarea = st.date_input("Fecha de entrega", value=f_hoy + datetime.timedelta(days=7))
                    desc_tarea = st.text_area("Descripción de la tarea")
                    if st.form_submit_button("💾 GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_age]["id"],
                            "fecha": str(f_hoy),
                            "contenido_clase": temas,
                            "tarea_proxima": desc_tarea,
                            "fecha_tarea": str(f_tarea)
                        }).execute()
                        st.success("Agenda y Tarea guardadas.")
                        st.rerun()
        else: st.info("Cree un curso primero.")

    # --- TAB 1: ALUMNOS (FILTROS + INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("f_new_al"):
                nn = st.text_input("Nombre")
                na = st.text_input("Apellido")
                nc = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    res = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if res.data:
                        supabase.table("inscripciones").insert({"alumno_id": res.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc}).execute()
                        st.rerun()
        
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_mat = c1.selectbox("📍 Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v129_f_m")
        f_bus = c2.text_input("🔍 Apellido/Nombre:", key="v129_f_b").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_l.data:
            for it in r_l.data:
                al = it['alumnos']
                if (f_mat == "Todas" or it['nombre_curso_materia'] == f_mat) and (f_bus in al['nombre'].lower() or f_bus in al['apellido'].lower()):
                    with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                        with st.form(f"ed_al_{it['id']}"):
                            st.text_input("Nombre", value=al['nombre'])
                            st.text_input("Apellido", value=al['apellido'])
                            b1, b2, b3 = st.columns(3)
                            if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                            if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                            if b3.form_submit_button("🗑️ BORRAR"):
                                supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                st.rerun()

    # --- TAB 2: ASISTENCIA (CORREGIDA) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Materia:", ["---"] + list(mapa_cursos.keys()), key="v129_as_c")
            f_as_n = ac2.text_input("Buscar Alumno:", key="v129_as_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if f_as_c != "---":
                r_as = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_as_c).not_.is_("alumno_id", "null").execute()
                if r_as.data:
                    for it in r_as.data:
                        al = it['alumnos']
                        if f_as_n in al['apellido'].lower() or f_as_n in al['nombre'].lower():
                            with st.expander(f"📌 ASISTENCIA: {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_as_{al['id']}"):
                                    est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                    c1, c2, c3 = st.columns(3)
                                    if c1.form_submit_button("💾 GUARDAR"):
                                        supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": f_as_c, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                        st.success("Guardado")
                                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
        else: st.warning("Cree un curso primero.")

    # --- TAB 3: NOTAS (FUNCIONAL) ---
    with tabs[3]:
        st.subheader("📝 Carga de Notas")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            nc1, nc2 = st.columns(2)
            f_nt_c = nc1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="v129_nt_c")
            f_nt_n = nc2.text_input("Alumno:", key="v129_nt_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if f_nt_c != "---":
                r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_c).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_nt_n in al['apellido'].lower():
                            with st.expander(f"📝 NOTA: {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"f_nt_{al['id']}"):
                                    vn = st.text_input("Nota")
                                    vi = st.text_input("Instancia")
                                    nb1, nb2, nb3 = st.columns(3)
                                    if nb1.form_submit_button("💾 GUARDAR"):
                                        supabase.table("notas").insert({"alumno_id": al['id'], "materia": f_nt_c, "nota": vn, "descripcion": vi}).execute()
                                        st.success("Nota guardada")
                                    if nb2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if nb3.form_submit_button("🗑️ BORRAR"): st.rerun()
        else: st.info("Cree un curso primero.")

    # --- TAB 4: CURSOS (ACTIVO/INACTIVO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("v129_new_c"):
            n_c = st.text_input("Nombre de Materia")
            if st.form_submit_button("➕ CREAR MATERIA"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_c, "estado": "ACTIVO"}).execute()
                st.rerun()
        st.divider()
        for n, info in mapa_cursos.items():
            est_css = "st-active" if info["estado"] == "ACTIVO" else "st-inactive"
            with st.expander(f"📘 {n}"):
                st.markdown(f'<span class="{est_css}">{info["estado"]}</span>', unsafe_allow_html=True)
                with st.form(f"ed_c_{info['id']}"):
                    st.text_input("Materia", value=n)
                    nuevo_est = st.selectbox("Cambiar Estado:", ["ACTIVO", "INACTIVO"], index=0 if info["estado"] == "ACTIVO" else 1)
                    cb1, cb2, cb3 = st.columns(3)
                    if cb1.form_submit_button("💾 GUARDAR"):
                        supabase.table("inscripciones").update({"estado": nuevo_est}).eq("id", info['id']).execute()
                        st.rerun()
                    if cb2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if cb3.form_submit_button("🗑️ BORRAR DEFINITIVAMENTE"):
                        supabase.table("inscripciones").delete().eq("id", info['id']).execute()
                        st.rerun()
