import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

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
        with st.form("login_v138"):
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
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"Sede: {u_data['email'].split('.')[0].capitalize()}")
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (BUSCADORES + CARGA) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if not mapa_cursos:
            st.warning("Debe crear una materia primero.")
        else:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            sel_cur = c1.selectbox("📍 Filtrar Curso:", ["Seleccione..."] + list(mapa_cursos.keys()), key="as_cur")
            bus_nom = c2.text_input("🔍 Buscar por Apellido:", key="as_nom").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if sel_cur != "Seleccione...":
                r_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_cur).not_.is_("alumno_id", "null").execute()
                for it in r_al.data:
                    al = it['alumnos']
                    if bus_nom in al['apellido'].lower() or bus_nom in al['nombre'].lower():
                        with st.expander(f"📌 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"f_as_{al['id']}"):
                                est_as = st.radio("Asistencia:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                                if st.form_submit_button("💾 GUARDAR"):
                                    supabase.table("asistencia").insert({
                                        "alumno_id": al['id'], 
                                        "materia": sel_cur, 
                                        "estado": est_as, 
                                        "fecha": str(datetime.date.today())
                                    }).execute()
                                    st.success("Registrado.")

    # --- TAB 3: NOTAS (BUSCADORES + CARGA) ---
    with tabs[3]:
        st.subheader("📝 Registro de Calificaciones")
        if not mapa_cursos:
            st.warning("Debe crear una materia primero.")
        else:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            n1, n2 = st.columns(2)
            sel_cur_n = n1.selectbox("📍 Filtrar Curso:", ["Seleccione..."] + list(mapa_cursos.keys()), key="nt_cur")
            bus_nom_n = n2.text_input("🔍 Buscar por Apellido:", key="nt_nom").lower()
            st.markdown('</div>', unsafe_allow_html=True)

            if sel_cur_n != "Seleccione...":
                r_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_cur_n).not_.is_("alumno_id", "null").execute()
                for it in r_al_n.data:
                    al = it['alumnos']
                    if bus_nom_n in al['apellido'].lower():
                        with st.expander(f"📝 {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"f_nt_{al['id']}"):
                                t_nt = st.selectbox("Tipo:", ["Examen", "Trabajo Práctico", "Concepto"])
                                val_nt = st.number_input("Nota", 1, 10, 7)
                                if st.form_submit_button("💾 REGISTRAR NOTA"):
                                    supabase.table("notas").insert({
                                        "alumno_id": al['id'],
                                        "materia": sel_cur_n,
                                        "tipo_nota": t_nt,
                                        "calificacion": val_nt,
                                        "fecha": str(datetime.date.today())
                                    }).execute()
                                    st.success("Nota guardada.")

    # --- TAB 4: CURSOS (GRABACIÓN FIJA) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("crear_c_v138"):
            nom_c = st.text_input("Nombre de Materia")
            if st.form_submit_button("💾 GRABAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nom_c, "anio_lectivo": 2026}).execute()
                st.rerun()
        st.divider()
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                c1, c2 = st.columns(2)
                if c1.button("BORRAR", key=f"del_{i}"):
                    supabase.table("inscripciones").delete().eq("id", i).execute()
                    st.rerun()

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            sel_ag = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()))
            if sel_ag != "---":
                with st.form("f_ag_138"):
                    t_c = st.text_area("Temas")
                    f_t = st.date_input("Entrega Tarea")
                    d_t = st.text_area("Tarea")
                    if st.form_submit_button("GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag], "fecha": str(datetime.date.today()), "contenido_clase": t_c, "tarea_proxima": d_t, "fecha_tarea": str(f_t)}).execute()
                        st.success("Ok.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        if mapa_cursos:
            with st.expander("➕ INSCRIBIR"):
                with st.form("ins_al_138"):
                    nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                    nc = st.selectbox("Curso", list(mapa_cursos.keys()))
                    if st.form_submit_button("REGISTRAR"):
                        res_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc}).execute()
                            st.rerun()
