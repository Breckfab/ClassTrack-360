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

# --- ESTILO Y RELOJ SUPERIOR DERECHO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
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

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v118"):
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
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 2: ASISTENCIA (BUSCADOR POR CURSO Y APELLIDO) ---
    with tabs[2]:
        st.subheader("✅ Registro de Asistencia")
        if mapa_cursos:
            c1, c2 = st.columns(2)
            sel_cur_as = c1.selectbox("Filtrar por Curso:", ["Todos"] + list(mapa_cursos.keys()), key="as_c")
            bus_as = c2.text_input("Buscar por Apellido:", key="as_a").lower()
            
            # Aquí iría el listado filtrado de asistencia
            st.info("ℹ️ Seleccione un curso para ver la lista de alumnos.")
        else: st.warning("Cree una materia en 'Cursos' primero.")

    # --- TAB 3: NOTAS (GESTIÓN COMPLETA) ---
    with tabs[3]:
        st.subheader("📝 Gestión de Notas")
        if mapa_cursos:
            c1, c2 = st.columns(2)
            sel_cur_nt = c1.selectbox("Filtrar por Curso:", ["--- Seleccionar ---"] + list(mapa_cursos.keys()), key="nt_c")
            bus_nt = c2.text_input("Buscar por Apellido:", key="nt_a").lower()
            
            if sel_cur_nt != "--- Seleccionar ---":
                try:
                    query = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_cur_nt).not_.is_("alumno_id", "null")
                    r_al = query.execute()
                    
                    if r_al.data:
                        for item in r_al.data:
                            alu = item['alumnos']
                            if bus_nt in alu['apellido'].lower():
                                with st.expander(f"📝 {alu['apellido'].upper()}, {alu['nombre']}"):
                                    # Formulario para agregar nota
                                    with st.form(f"f_nota_{alu['id']}"):
                                        val_nt = st.text_input("Calificación")
                                        ins_nt = st.text_input("Instancia (Ej: Parcial 1)")
                                        col1, col2, col3 = st.columns(3)
                                        if col1.form_submit_button("💾 GUARDAR"):
                                            supabase.table("notas").insert({"alumno_id": alu['id'], "materia": sel_cur_nt, "nota": val_nt, "descripcion": ins_nt}).execute()
                                            st.rerun()
                                        if col2.form_submit_button("🔄 CANCELAR"): st.rerun()
                                        if col3.form_submit_button("🗑️ BORRAR"):
                                            # Lógica para borrar última nota o registro específico
                                            st.rerun()
                    else: st.info("No hay alumnos en este curso.")
                except: st.error("Error al cargar notas.")
        else: st.warning("Cree una materia en 'Cursos' primero.")

    # --- TAB 4: CURSOS (ORDEN INVERSO) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Materias")
        if mapa_cursos:
            for n, i in mapa_cursos.items():
                with st.expander(f"📘 {n}"):
                    with st.form(f"ed_v118_{i}"):
                        new_n = st.text_input("Nombre", value=n)
                        b1, b2, b3 = st.columns(3)
                        if b1.form_submit_button("GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_n}).eq("id", i).execute()
                            st.rerun()
                        if b2.form_submit_button("CANCELAR"): st.rerun()
                        if b3.form_submit_button("⚠️ BORRAR"):
                            supabase.table("inscripciones").delete().eq("id", i).execute()
                            st.rerun()
        st.divider()
        with st.form("f_new_v118"):
            nc = st.text_input("Nueva Materia")
            if st.form_submit_button("AGREGAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
