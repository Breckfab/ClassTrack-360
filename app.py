import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v142", layout="wide")

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
        with st.form("login_v142"):
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
                        else: st.error("Acceso denegado.")
                    except: st.error("Error de conexión.")
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

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN RESTABLECIDA) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_m_al = c1.selectbox("Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="v142_f_m_al")
        f_n_al = c2.text_input("Buscar Apellido:", key="v142_f_n_al").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("➕ INSCRIBIR NUEVO ALUMNO", expanded=False):
            with st.form("form_inscripcion_v142", clear_on_submit=True):
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                cur_a = st.selectbox("Asignar a:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin materias"])
                if st.form_submit_button("💾 REGISTRAR E INSCRIBIR"):
                    if nom_a and ape_a and mapa_cursos:
                        res_al = supabase.table("alumnos").insert({"nombre": nom_a, "apellido": ape_a}).execute()
                        if res_al.data:
                            supabase.table("inscripciones").insert({
                                "alumno_id": res_al.data[0]['id'],
                                "profesor_id": u_data['id'],
                                "nombre_curso_materia": cur_a,
                                "anio_lectivo": 2026
                            }).execute()
                            st.success(f"✅ {ape_a} inscripto en {cur_a}.")
                            st.rerun()
        st.divider()
        try:
            r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_l.data:
                for it in r_l.data:
                    al = it['alumnos']
                    if (f_m_al == "Todas" or it['nombre_curso_materia'] == f_m_al) and (f_n_al in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} | {it['nombre_curso_materia']}"):
                            with st.form(f"ed_al_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3)
                                if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                                if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if b3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
        except: pass

    # --- TAB 2: ASISTENCIA (CARGA RESTABLECIDA) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if not mapa_cursos:
            st.info("Cree una materia en 'Cursos' primero.")
        else:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            sel_as_c = ac1.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="v142_as_c")
            sel_as_n = ac2.text_input("Buscar Alumno:", key="v142_as_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if sel_as_c != "---":
                r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as_c).not_.is_("alumno_id", "null").execute()
                for it in r_as.data:
                    al = it['alumnos']
                    if sel_as_n in al['apellido'].lower():
                        with st.expander(f"📌 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"f_as_{al['id']}"):
                                est_as = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("💾 GRABAR ASISTENCIA"):
                                    supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": sel_as_c, "estado": est_as, "fecha": str(datetime.date.today())}).execute()
                                    st.success("Grabado.")
                                if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if c3.form_submit_button("🗑️ BORRAR"): st.rerun()

    # --- TAB 4: CURSOS (LISTADO RESTABLECIDO) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("crear_c_v142"):
            new_c = st.text_input("Nombre de nueva materia")
            if st.form_submit_button("💾 GRABAR NUEVA MATERIA"):
                if new_c:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": new_c, "anio_lectivo": 2026}).execute()
                    st.rerun()
        st.divider()
        st.write("### Listado de Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ops_c_{i}"):
                        st.text_input("Nombre", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("💾 GUARDAR"): st.rerun()
                        if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                        if c3.form_submit_button("🗑️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        else:
            st.info("No hay materias registradas.")

    # --- TAB 0: AGENDA Y TAB 3: NOTAS ---
    with tabs[0]: st.subheader("📅 Agenda"); st.info("Seleccione un curso arriba.")
    with tabs[3]: st.subheader("📝 Notas"); st.info("Seleccione un curso arriba.")
