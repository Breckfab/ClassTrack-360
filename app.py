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

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
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

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v137"):
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
        st.write(f"Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        st.divider()
        if st.button("SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA DE MATERIAS (Jerarquía Principal) ---
    mapa_cursos = {}
    try:
        # Se eliminó el campo 'estado' de la consulta para evitar errores
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (GRABACIÓN CORREGIDA) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Materias")
        with st.form("crear_mat_v137", clear_on_submit=True):
            st.write("### ➕ Registrar Nueva Materia")
            nueva_m = st.text_input("Nombre de la Materia / Curso")
            if st.form_submit_button("💾 GRABAR MATERIA"):
                if nueva_m:
                    try:
                        # Se graban solo las columnas que existen según tu estructura
                        supabase.table("inscripciones").insert({
                            "profesor_id": u_data['id'],
                            "nombre_curso_materia": nueva_m,
                            "anio_lectivo": 2026
                        }).execute()
                        st.success(f"✅ Materia '{nueva_m}' grabada con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al grabar: {e}")
                else:
                    st.warning("Ingrese un nombre.")

        st.divider()
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ops_c_{i}"):
                        new_n = st.text_input("Materia", value=n)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_n}).eq("id", i).execute()
                            st.rerun()
                        if c2.form_submit_button("CANCELAR"): st.rerun()
                        if c3.form_submit_button("BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        else:
            st.info("No hay materias. Use el formulario superior.")

    # --- TAB 1: ALUMNOS (FILTROS Y CARGA) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            if not mapa_cursos:
                st.warning("Cree una materia primero.")
            else:
                with st.form("f_ins_al_v137"):
                    nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                    nc = st.selectbox("Curso:", list(mapa_cursos.keys()))
                    if st.form_submit_button("💾 REGISTRAR"):
                        r_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                        if r_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": r_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc}).execute()
                            st.rerun()
        
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        f_m = fc1.selectbox("Curso:", ["Todas"] + list(mapa_cursos.keys()), key="f_al_c_137")
        f_b = fc2.text_input("Buscar Apellido:", key="f_al_b_137").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        try:
            r_l = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_l.data:
                for it in r_l.data:
                    al = it['alumnos']
                    if (f_m == "Todas" or it['nombre_curso_materia'] == f_m) and (f_b in al['apellido'].lower()):
                        with st.expander(f"{al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                            with st.form(f"ed_al_{it['id']}"):
                                st.text_input("Nombre", value=al['nombre'])
                                st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3)
                                if b1.form_submit_button("GUARDAR"): st.rerun()
                                if b2.form_submit_button("CANCELAR"): st.rerun()
                                if b3.form_submit_button("BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
        except: pass

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            sel_ag = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="ag_137")
            if sel_ag != "---":
                with st.form("f_ag_v137"):
                    st.write(f"Hoy: {datetime.date.today().strftime('%d/%m/%Y')}")
                    temas = st.text_area("Dictado hoy")
                    f_ent = st.date_input("Próxima tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    desc_t = st.text_area("Tarea")
                    if st.form_submit_button("💾 GUARDAR"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag], "fecha": str(datetime.date.today()), "contenido_clase": temas, "tarea_proxima": desc_t, "fecha_tarea": str(f_ent)}).execute()
                        st.success("Guardado.")
