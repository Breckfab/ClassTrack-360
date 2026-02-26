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

# --- RELOJ ---
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

# --- LÓGICA DE LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v126"):
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
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE MATERIAS ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN + EDICIÓN + FILTROS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        # Sector de Inscripción Nueva
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO", expanded=False):
            with st.form("ins_n_al"):
                ni_n = st.text_input("Nombre")
                ni_a = st.text_input("Apellido")
                ni_c = st.selectbox("Asignar a Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR E INSCRIBIR"):
                    # 1. Crear Alumno
                    r_new_al = supabase.table("alumnos").insert({"nombre": ni_n, "apellido": ni_a}).execute()
                    if r_new_al.data:
                        # 2. Inscribir en materia
                        supabase.table("inscripciones").insert({
                            "alumno_id": r_new_al.data[0]['id'],
                            "profesor_id": u_data['id'],
                            "nombre_curso_materia": ni_c
                        }).execute()
                        st.success("✅ Alumno inscripto correctamente.")
                        st.rerun()

        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        f_cur = c1.selectbox("📍 Filtrar por Materia:", ["Todas"] + list(mapa_cursos.keys()), key="f_al_c")
        f_nom = c2.text_input("🔍 Buscar Nombre/Apellido:", key="f_al_n").lower()
        st.markdown('</div>', unsafe_allow_html=True)
        
        try:
            r_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_al.data:
                for it in r_al.data:
                    al = it['alumnos']
                    if (f_cur == "Todas" or it['nombre_curso_materia'] == f_cur) and (f_nom in al['nombre'].lower() or f_nom in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} ({it['nombre_curso_materia']})"):
                            with st.form(f"ed_al_{it['id']}"):
                                en_n = st.text_input("Nombre", value=al['nombre'])
                                en_a = st.text_input("Apellido", value=al['apellido'])
                                b1, b2, b3 = st.columns(3)
                                if b1.form_submit_button("💾 GUARDAR"):
                                    supabase.table("alumnos").update({"nombre": en_n, "apellido": en_a}).eq("id", al['id']).execute()
                                    st.rerun()
                                if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if b3.form_submit_button("🗑️ BORRAR DEFINITIVAMENTE"):
                                    supabase.table("inscripciones").delete().eq("id", it['id']).execute()
                                    st.rerun()
        except: st.error("Error al cargar alumnos.")

    # --- TAB 3: NOTAS (CARGA REAL DE CALIFICACIONES) ---
    with tabs[3]:
        st.subheader("📝 Registro de Calificaciones")
        if mapa_cursos:
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            nc1, nc2 = st.columns(2)
            f_nt_c = nc1.selectbox("📍 Curso/Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="f_nt_c")
            f_nt_n = nc2.text_input("🔍 Apellido del Alumno:", key="f_nt_n").lower()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if f_nt_c != "--- Seleccionar ---":
                r_nt = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nt_c).not_.is_("alumno_id", "null").execute()
                if r_nt.data:
                    for it in r_nt.data:
                        al = it['alumnos']
                        if f_nt_n in al['apellido'].lower():
                            with st.expander(f"📝 CALIFICAR A: {al['apellido'].upper()}, {al['nombre']}"):
                                with st.form(f"c_nt_{al['id']}"):
                                    v_nota = st.text_input("Nota (Ej: 8, 10, A)")
                                    v_inst = st.text_input("Instancia (Ej: 1er Parcial, Final)")
                                    c1, c2, c3 = st.columns(3)
                                    if c1.form_submit_button("💾 GUARDAR NOTA"):
                                        supabase.table("notas").insert({
                                            "alumno_id": al['id'],
                                            "materia": f_nt_c,
                                            "nota": v_nota,
                                            "descripcion": v_inst
                                        }).execute()
                                        st.success(f"Nota guardada para {al['nombre']}")
                                        st.rerun()
                                    if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                    if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
        else: st.info("Cree un curso primero en la pestaña 'Cursos'.")

    # --- TAB 0: AGENDA (RESTABLECIDA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            m_a = st.selectbox("Materia:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="ag_v126")
            if m_a != "--- Seleccionar ---":
                with st.form("f_ag_v126"):
                    f_hoy = datetime.date.today()
                    st.write(f"Registro: {f_hoy.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados hoy")
                    f_t = st.date_input("Próxima tarea", value=f_hoy + datetime.timedelta(days=7))
                    tarea = st.text_area("Descripción")
                    if st.form_submit_button("💾 GUARDAR CLASE"):
                        supabase.table("bitacora").insert({
                            "inscripcion_id": mapa_cursos[m_a],
                            "fecha": str(f_hoy),
                            "contenido_clase": temas,
                            "tarea_proxima": tarea,
                            "fecha_tarea": str(f_t)
                        }).execute()
                        st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("n_c_v126"):
            n_cur = st.text_input("Nombre de la nueva Materia/Curso")
            if st.form_submit_button("➕ CREAR MATERIA"):
                supabase.table("inscripciones").insert({
                    "profesor_id": u_data['id'],
                    "nombre_curso_materia": n_cur
                }).execute()
                st.rerun()
        st.divider()
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                with st.form(f"c_ed_{i}"):
                    st.text_input("Nombre", value=n)
                    b1, b2, b3 = st.columns(3)
                    if b1.form_submit_button("💾 GUARDAR"): st.rerun()
                    if b2.form_submit_button("🔄 CANCELAR"): st.rerun()
                    if b3.form_submit_button("🗑️ BORRAR"):
                        supabase.table("inscripciones").delete().eq("id", i).execute()
                        st.rerun()
