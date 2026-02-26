import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v131", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .st-inactive { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; background: rgba(255,75,75,0.1); }
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
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

# --- LÓGICA DE ACCESO ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v131"):
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
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        st.divider()
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA DE CURSOS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, estado").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: {"id": row['id'], "estado": row.get('estado', 'ACTIVO')} for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clases")
        if mapa_cursos:
            m_age = st.selectbox("Elegir Materia:", ["---"] + list(mapa_cursos.keys()), key="v131_ag")
            if m_age != "---":
                with st.form("f_age_v131"):
                    f_hoy = datetime.date.today()
                    st.write(f"Fecha: {f_hoy.strftime('%d/%m/%Y')}")
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
                        st.success("✅ Guardado.")
                        st.rerun()
        else: st.info("ℹ️ No hay materias creadas.")

    # --- TAB 1: ALUMNOS (FILTROS + INSCRIPCIÓN) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("f_ins_v131"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Asignar a Curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Debe crear un curso"])
                if st.form_submit_button("💾 REGISTRAR E INSCRIBIR"):
                    r_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na, "estado": "ACTIVO"}).execute()
                    if r_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": r_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                        st.rerun()
        
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_m = c1.selectbox("📍 Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v131_f_m")
        f_n = c2.text_input("🔍 Buscar por Apellido/Nombre:", key="v131_f_b").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        try:
            r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_l.data:
                for it in r_l.data:
                    al = it['alumnos']
                    if (f_m == "Todas" or it['nombre_curso_materia'] == f_m) and (f_n in al['nombre'].lower() or f_n in al['apellido'].lower()):
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
            else: st.info("ℹ️ No hay alumnos inscriptos.")
        except: st.error("Error al conectar con la base de alumnos.")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            f_as_c = ac1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="v131_as_c")
            f_as_n = ac2.text_input("Alumno:", key="v131_as_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)
            if f_as_c != "---":
                st.info(f"Mostrando lista para {f_as_c}...")
        else: st.info("Cree un curso primero.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        st.subheader("📝 Carga de Notas")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            nc1, nc2 = st.columns(2)
            f_nt_c = nc1.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="v131_nt_c")
            f_nt_n = nc2.text_input("Apellido:", key="v131_nt_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)
            if f_nt_c != "---":
                st.info(f"Planilla de notas para {f_nt_c} activa.")
        else: st.info("Cree un curso primero.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("v131_new_c"):
            n_mat = st.text_input("Nombre de la nueva Materia")
            if st.form_submit_button("➕ CREAR MATERIA"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_mat, "estado": "ACTIVO"}).execute()
                st.rerun()
        st.divider()
        if mapa_cursos:
            for n, info in mapa_cursos.items():
                est_css = "st-active" if info["estado"] == "ACTIVO" else "st-inactive"
                with st.expander(f"📘 {n}"):
                    st.markdown(f'<span class="{est_css}">{info["estado"]}</span>', unsafe_allow_html=True)
                    with st.form(f"ed_c_{info['id']}"):
                        st.text_input("Materia", value=n)
                        cb1, cb2, cb3 = st.columns(3)
                        if cb1.form_submit_button("💾 GUARDAR"): st.rerun()
                        if cb2.form_submit_button("🔄 CANCELAR"): st.rerun()
                        if cb3.form_submit_button("🗑️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", info['id']).execute()
                            st.rerun()
        else: st.info("ℹ️ No hay cursos activos.")
