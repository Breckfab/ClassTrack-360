import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v128", layout="wide")

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

# --- RELOJ SUPERIOR DERECHO ---
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
        with st.form("login_v128"):
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
    
    # --- CARGA DE MATERIAS (Jerarquía Principal) ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN + FILTROS VISIBLES) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        # 1. Botón para Inscribir
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO EN UN CURSO"):
            with st.form("form_alta_alu"):
                new_n = st.text_input("Nombre")
                new_a = st.text_input("Apellido")
                new_c = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 GUARDAR E INSCRIBIR"):
                    r_alu = supabase.table("alumnos").insert({"nombre": new_n, "apellido": new_a}).execute()
                    if r_alu.data:
                        supabase.table("inscripciones").insert({
                            "alumno_id": r_alu.data[0]['id'],
                            "profesor_id": u_data['id'],
                            "nombre_curso_materia": new_c
                        }).execute()
                        st.success("Alumno inscripto.")
                        st.rerun()

        st.divider()
        
        # 2. Bloque de Filtros (Siempre presentes)
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        f_col1, f_col2 = st.columns(2)
        filtro_materia = f_col1.selectbox("📍 Filtrar por Curso:", ["Todas"] + list(mapa_cursos.keys()), key="f_m_al")
        filtro_nombre = f_col2.text_input("🔍 Buscar por Apellido/Nombre:", key="f_n_al").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. Lista de Alumnos con Triple Botonera
        try:
            r_list = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if r_list.data:
                for it in r_list.data:
                    al = it['alumnos']
                    if (filtro_materia == "Todas" or it['nombre_curso_materia'] == filtro_materia) and (filtro_nombre in al['nombre'].lower() or filtro_nombre in al['apellido'].lower()):
                        with st.expander(f"👤 {al['apellido'].upper()}, {al['nombre']} | {it['nombre_curso_materia']}"):
                            with st.form(f"edit_alu_{it['id']}"):
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
        except: st.error("Error al cargar lista.")

    # --- TAB 3: NOTAS (FILTROS + CARGA REAL) ---
    with tabs[3]:
        st.subheader("📝 Registro de Calificaciones")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        n_col1, n_col2 = st.columns(2)
        f_nota_mat = n_col1.selectbox("📍 Elegir Curso para Calificar:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="f_n_mat")
        f_nota_nom = n_col2.text_input("🔍 Buscar Alumno por Apellido:", key="f_n_nom").lower()
        st.markdown('</div>', unsafe_allow_html=True)

        if f_nota_mat != "--- Seleccionar ---":
            r_notas = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", f_nota_mat).not_.is_("alumno_id", "null").execute()
            if r_notas.data:
                for it in r_notas.data:
                    al = it['alumnos']
                    if f_nota_nom in al['apellido'].lower():
                        with st.expander(f"📝 CALIFICAR A: {al['apellido'].upper()}, {al['nombre']}"):
                            with st.form(f"form_nota_{al['id']}"):
                                v_n = st.text_input("Nota (Ej: 10)")
                                v_i = st.text_input("Instancia (Ej: Examen Final)")
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("💾 GUARDAR NOTA"):
                                    supabase.table("notas").insert({"alumno_id": al['id'], "materia": f_nota_mat, "nota": v_n, "descripcion": v_i}).execute()
                                    st.success("Nota guardada.")
                                if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                if c3.form_submit_button("🗑️ BORRAR"): st.rerun()
            else: st.warning("No hay alumnos en este curso.")

    # --- TAB 0: AGENDA (FECHA DE HOY) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            m_age = st.selectbox("Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()))
            if m_age != "--- Seleccionar ---":
                with st.form("f_agenda"):
                    st.write(f"Fecha de hoy: {datetime.date.today().strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas dictados")
                    if st.form_submit_button("💾 GUARDAR CLASE"): st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Materias")
        with st.form("new_cur"):
            nc = st.text_input("Nombre de Materia")
            if st.form_submit_button("➕ CREAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc}).execute()
                st.rerun()
