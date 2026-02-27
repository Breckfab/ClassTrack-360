import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v199", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO, RELOJ Y FECHA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# RELOJ Y FECHA DINÁMICOS
components.html("""
    <div id="info-superior">
        <div id="fecha-actual" style="font-size: 0.9rem; color: #e0e0e0;">--/--/----</div>
        <div id="reloj-fijo" style="font-size: 1.2rem; color: #4facfe; font-weight: bold;">00:00:00</div>
    </div>
    <script>
    function actualizarInfo() {
        const ahora = new Date();
        const d = String(ahora.getDate()).padStart(2, '0');
        const m = String(ahora.getMonth() + 1).padStart(2, '0');
        const a = ahora.getFullYear();
        const h = String(ahora.getHours()).padStart(2, '0');
        const min = String(ahora.getMinutes()).padStart(2, '0');
        const s = String(ahora.getSeconds()).padStart(2, '0');
        window.parent.document.getElementById('fecha-actual').innerText = d + '/' + m + '/' + a;
        window.parent.document.getElementById('reloj-fijo').innerText = h + ':' + min + ':' + s;
    }
    setInterval(actualizarInfo, 1000); actualizarInfo();
    </script>
    """, height=60)

if st.session_state.user is None:
    st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    # --- MOTOR DE CONSULTAS (FIX) ---
    res_cursos = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_cursos.data} if res_cursos.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (RECUPERADO) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Cursos")
        if res_cursos.data:
            for c in res_cursos.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                    col1, col2, _ = st.columns([1,1,6])
                    col1.button("✏️ Editar", key=f"ed_c_{c['id']}")
                    if col2.button("🗑️ Borrar", key=f"del_c_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                        st.rerun()
        
        with st.expander("➕ CREAR NUEVO CURSO", expanded=not res_cursos.data):
            with st.form("new_cur"):
                n = st.text_input("Nombre de Materia")
                d = st.text_input("Días y Horarios")
                if st.form_submit_button("💾 GUARDAR CURSO"):
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{n} - {d}", "anio_lectivo": 2026}).execute()
                    st.rerun()

    # --- TAB 1: ALUMNOS (RECUPERADO) ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        if not mapa_cursos:
            st.warning("⚠️ Primero cree un curso en la pestaña 'Cursos'.")
        else:
            with st.form("ins_al", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom, ape = c1.text_input("Nombre"), c1.text_input("Apellido")
                dni = c2.text_input("DNI")
                cur_sel = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 GUARDAR E INSCRIBIR"):
                    if nom and ape and dni:
                        res_a = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape, "dni": dni}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": cur_sel, "anio_lectivo": 2026}).execute()
                            st.success(f"✅ Inscripción satisfactoria."); time.sleep(0.5); st.rerun()

            st.divider()
            st.write("### Listado de Alumnos")
            res_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if res_al.data:
                for r in res_al.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b> | {r["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                        b1, b2, _ = st.columns([1,1,6])
                        b1.button("✏️ Editar", key=f"ed_al_{r['id']}")
                        if b2.button("🗑️ Borrar", key=f"del_al_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
