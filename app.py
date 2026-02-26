import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="ClassTrack 360", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .st-inactive { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; background: rgba(255,75,75,0.1); }
    </style>
    """, unsafe_allow_html=True)

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

if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v130"):
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
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, estado").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: {"id": row['id'], "estado": row.get('estado', 'ACTIVO')} for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    with tabs[0]:
        st.subheader("Agenda de Clases")
        if mapa_cursos:
            m_age = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="v130_ag")
            if m_age != "---":
                with st.form("f_age_v130"):
                    f_hoy = datetime.date.today()
                    st.write(f"Fecha: {f_hoy.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados")
                    f_tarea = st.date_input("Fecha tarea", value=f_hoy + datetime.timedelta(days=7))
                    desc_tarea = st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[m_age]["id"], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": desc_tarea, "fecha_tarea": str(f_tarea)}).execute()
                        st.success("Guardado.")
                        st.rerun()

    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        with st.expander("Inscribir Alumno Nuevo"):
            with st.form("f_ins_v130"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("INSCRIBIR"):
                    r_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                    if r_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": r_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "estado": "ACTIVO"}).execute()
                        st.rerun()
        
        bus = st.text_input("Buscar por Apellido:", key="v130_bus").lower()
        r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if r_l.data:
            for it in r_l.data:
                al = it['alumnos']
                if bus in al['apellido'].lower():
                    with st.expander(f"{al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                        with st.form(f"ed_al_{it['id']}"):
                            st.text_input("Nombre", value=al['nombre'])
                            st.text_input("Apellido", value=al['apellido'])
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("GUARDAR"): st.rerun()
                            if c2.form_submit_button("CANCELAR"): st.rerun()
                            if c3.form_submit_button("BORRAR"):
                                supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                st.rerun()

    with tabs[2]:
        st.subheader("Asistencia")
        if mapa_cursos:
            m_as = st.selectbox("Materia:", ["---"] + list(mapa_cursos.keys()), key="v130_as")
            if m_as != "---":
                r_as = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", m_as).not_.is_("alumno_id", "null").execute()
                for it in r_as.data:
                    al = it['alumnos']
                    with st.expander(f"{al['apellido'].upper()}, {al['nombre']}"):
                        with st.form(f"as_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": m_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Registrado.")

    with tabs[4]:
        st.subheader("Cursos")
        with st.form("n_c_v130"):
            n_mat = st.text_input("Nombre de Materia")
            if st.form_submit_button("CREAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_mat, "estado": "ACTIVO"}).execute()
                st.rerun()
        for n, info in mapa_cursos.items():
            est_css = "st-active" if info["estado"] == "ACTIVO" else "st-inactive"
            with st.expander(f"{n}"):
                st.markdown(f'<span class="{est_css}">{info["estado"]}</span>', unsafe_allow_html=True)
                with st.form(f"ed_c_{info['id']}"):
                    st.text_input("Materia", value=n)
                    nuevo_est = st.selectbox("Estado:", ["ACTIVO", "INACTIVO"], index=0 if info["estado"] == "ACTIVO" else 1)
                    cb1, cb2, cb3 = st.columns(3)
                    if cb1.form_submit_button("GUARDAR"):
                        supabase.table("inscripciones").update({"estado": nuevo_est}).eq("id", info['id']).execute()
                        st.rerun()
                    if cb2.form_submit_button("CANCELAR"): st.rerun()
                    if cb3.form_submit_button("BORRAR"):
                        supabase.table("inscripciones").delete().eq("id", info['id']).execute()
                        st.rerun()
