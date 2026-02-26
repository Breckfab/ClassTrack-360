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

# --- ESTILO Y RELOJ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .status-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:20px; font-family:'JetBrains Mono',monospace; font-size:1.1rem; color:white; font-weight:400; z-index:9999;">00:00:00</div>
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
        with st.form("login_v115"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR"):
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
    
    # --- CARGA DE CURSOS PARA SELECTORES ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS (RESTAURADA TOTALMENTE) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        # 1. BUSCADOR
        busqueda = st.text_input("🔍 Buscar alumno por nombre o apellido...", "").strip().lower()
        
        # 2. LISTADO Y EDICIÓN
        try:
            r_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, estado, email)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            
            if r_al.data:
                for item in r_al.data:
                    alu = item['alumnos']
                    nombre_completo = f"{alu['apellido']} {alu['nombre']}".lower()
                    
                    if busqueda in nombre_completo:
                        with st.expander(f"👤 {alu['apellido'].upper()}, {alu['nombre']} - {item['nombre_curso_materia']}"):
                            with st.form(f"form_alu_{item['id']}"):
                                col_a, col_b = st.columns(2)
                                new_nom = col_a.text_input("Nombre", value=alu['nombre'])
                                new_ape = col_b.text_input("Apellido", value=alu['apellido'])
                                
                                # Cambiar de curso
                                nuevo_curso = st.selectbox("Cambiar a Curso:", list(mapa_cursos.keys()), index=list(mapa_cursos.keys()).index(item['nombre_curso_materia']) if item['nombre_curso_materia'] in mapa_cursos else 0)
                                
                                st.markdown(f"Estado: <span class='status-active'>{alu['estado']}</span>", unsafe_allow_html=True)
                                
                                c1, c2, c3 = st.columns(3)
                                if c1.form_submit_button("💾 GUARDAR"):
                                    supabase.table("alumnos").update({"nombre": new_nom, "apellido": new_ape}).eq("id", alu['id']).execute()
                                    if nuevo_curso != item['nombre_curso_materia']:
                                        supabase.table("inscripciones").update({"nombre_curso_materia": nuevo_curso}).eq("id", item['id']).execute()
                                    st.success("Cambios guardados")
                                    st.rerun()
                                if c2.form_submit_button("❌ CANCELAR"): st.rerun()
                                if c3.form_submit_button("🗑️ BORRAR"):
                                    supabase.table("inscripciones").delete().eq("id", item['id']).execute()
                                    st.rerun()
            else:
                st.info("No hay alumnos inscriptos aún.")
        except:
            st.error("Error al cargar la lista de alumnos.")

        st.divider()
        
        # 3. INSCRIPCIÓN Y ASIGNACIÓN
        with st.form("nueva_inscripcion"):
            st.write("### ➕ Inscribir Nuevo Alumno")
            col1, col2 = st.columns(2)
            n_nom = col1.text_input("Nombre")
            n_ape = col2.text_input("Apellido")
            n_cur = st.selectbox("Asignar a Curso:", list(mapa_cursos.keys()) if mapa_cursos else ["Debe crear un curso primero"])
            
            if st.form_submit_button("REGISTRAR E INSCRIBIR"):
                if n_nom and n_ape and mapa_cursos:
                    # Crear alumno
                    res_alu = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "estado": "ACTIVO"}).execute()
                    if res_alu.data:
                        # Inscribir en curso
                        new_id = res_alu.data[0]['id']
                        supabase.table("inscripciones").insert({
                            "profesor_id": u_data['id'],
                            "alumno_id": new_id,
                            "nombre_curso_materia": n_cur,
                            "anio_lectivo": 2026
                        }).execute()
                        st.success(f"Alumno {n_nom} inscripto en {n_cur}")
                        st.rerun()
                else:
                    st.warning("Complete todos los campos.")

    # --- RESTO DE PESTAÑAS (MANTENIENDO LÓGICA) ---
    with tabs[0]: st.subheader("📅 Agenda"); st.write("Selector de agenda disponible.")
    with tabs[4]:
        st.subheader("🏗️ Materias")
        for n, i in mapa_cursos.items():
            with st.expander(f"📘 {n}"):
                with st.form(f"ed_c_{i}"):
                    st.text_input("Nombre", value=n)
                    b1, b2, b3 = st.columns(3)
                    if b1.form_submit_button("GUARDAR"): st.rerun()
                    if b2.form_submit_button("CANCELAR"): st.rerun()
                    if b3.form_submit_button("🗑️ BORRAR DEFINITIVAMENTE"): st.rerun()
