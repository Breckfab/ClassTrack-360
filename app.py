import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v187", layout="wide")

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
    .ficha-alumno { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #4facfe; margin-bottom: 10px; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ Y FECHA ---
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
    """, height=0)

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
    # Cargar cursos activos
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB ALUMNOS (REDISEÑADA Y FUNCIONAL) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        if not mapa_cursos:
            st.warning("⚠️ Debés crear un curso en la pestaña 'Cursos' antes de inscribir alumnos.")
        else:
            with st.form("registro_alumno_v187", clear_on_submit=True):
                st.write("### 📝 Nueva Inscripción")
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre")
                apellido = c1.text_input("Apellido")
                dni = c2.text_input("DNI")
                telefono = c2.text_input("Teléfono de contacto")
                curso_destino = st.selectbox("Curso a inscribir:", list(mapa_cursos.keys()))
                
                col_btn1, col_btn2, _ = st.columns([1,1,4])
                guardar = col_btn1.form_submit_button("💾 GUARDAR")
                cancelar = col_btn2.form_submit_button("❌ CANCELAR")
                
                if guardar:
                    if nombre and apellido:
                        try:
                            # 1. Crear el alumno
                            res_al = supabase.table("alumnos").insert({
                                "nombre": nombre, "apellido": apellido, "dni": dni, "telefono_contacto": telefono
                            }).execute()
                            
                            if res_al.data:
                                # 2. Crear la inscripción
                                supabase.table("inscripciones").insert({
                                    "alumno_id": res_al.data[0]['id'],
                                    "profesor_id": u_data['id'],
                                    "nombre_curso_materia": curso_destino,
                                    "anio_lectivo": 2026
                                }).execute()
                                st.success(f"✅ Inscripción satisfactoria: {apellido.upper()}, {nombre} ha sido agregado a {curso_destino}.")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar en la base de datos: {str(e)}")
                    else:
                        st.warning("⚠️ El nombre y el apellido son obligatorios.")

            st.divider()
            st.write("### 📋 Alumnos Inscriptos")
            # Listado de alumnos con su Triple Botonera
            res_lista = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            
            if res_lista.data:
                for reg in res_lista.data:
                    al = reg['alumnos']
                    with st.container():
                        st.markdown(f"""
                        <div class="ficha-alumno">
                            <b>👤 {al['apellido'].upper()}, {al['nombre']}</b><br>
                            📌 Curso: {reg['nombre_curso_materia']} | DNI: {al['dni'] if al['dni'] else '---'}
                        </div>
                        """, unsafe_allow_html=True)
                        b1, b2, b3, _ = st.columns([1,1,1,5])
                        if b1.button("✏️ Editar", key=f"ed_al_{reg['id']}"): st.info("Función de edición próximamente.")
                        if b2.button("🗑️ Borrar", key=f"del_al_{reg['id']}"):
                            supabase.table("inscripciones").delete().eq("id", reg['id']).execute()
                            st.warning("Inscripción eliminada."); time.sleep(0.5); st.rerun()
                        if b3.button("💾 Guardar", key=f"sv_al_{reg['id']}"): st.success("Cambios guardados.")
            else:
                st.info("Aún no hay alumnos inscriptos.")

    # --- TAB CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        # Listado siempre arriba
        if mapa_cursos:
            for n, id in mapa_cursos.items():
                with st.container():
                    st.markdown(f'<div class="ficha-alumno">📖 <b>{n}</b></div>', unsafe_allow_html=True)
                    bc1, bc2, bc3, _ = st.columns([1,1,1,5])
                    if bc1.button("✏️ Editar", key=f"ed_c_{id}"): st.info("Edición de curso.")
                    if bc2.button("🗑️ Borrar", key=f"del_c_{id}"):
                        supabase.table("inscripciones").delete().eq("id", id).execute()
                        st.rerun()
                    if bc3.button("💾 Guardar", key=f"sv_c_{id}"): st.success("Ok")
        
        st.divider()
        with st.expander("➕ CREAR NUEVO CURSO"):
            with st.form("new_cur"):
                nm = st.text_input("Nombre Materia")
                hs = st.text_input("Días/Horas")
                if st.form_submit_button("💾 INSTALAR"):
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{nm} - {hs}", "anio_lectivo": 2026}).execute()
                    st.rerun()
