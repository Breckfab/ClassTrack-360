import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v188", layout="wide")

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
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB ALUMNOS (REDISEÑADA: ANTI-DUPLICADOS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        
        if not mapa_cursos:
            st.warning("⚠️ Debés crear un curso en la pestaña 'Cursos' antes de inscribir alumnos.")
        else:
            with st.form("registro_alumno_v188", clear_on_submit=True):
                st.write("### 📝 Nueva Inscripción")
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre")
                apellido = c1.text_input("Apellido")
                dni = c2.text_input("DNI")
                telefono = c2.text_input("Teléfono de contacto")
                curso_destino = st.selectbox("Curso a inscribir:", list(mapa_cursos.keys()))
                
                guardar = st.form_submit_button("💾 GUARDAR E INSCRIBIR")
                
                if guardar:
                    if nombre and apellido and dni:
                        # VERIFICACIÓN ANTI-DUPLICADOS
                        check = supabase.table("alumnos").select("id").eq("dni", dni).execute()
                        if check.data:
                            st.error(f"❌ El alumno con DNI {dni} ya existe en el sistema.")
                        else:
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
                                    st.success(f"✅ Inscripción satisfactoria: {apellido.upper()} agregado a {curso_destino}.")
                                    time.sleep(1)
                                    st.rerun()
                            except:
                                st.error("❌ Error de conexión al guardar.")
                    else:
                        st.warning("⚠️ Nombre, Apellido y DNI son obligatorios.")

            st.divider()
            st.write("### 📋 Alumnos Inscriptos")
            res_lista = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            
            if res_lista.data:
                # Convertir a DataFrame para visualización limpia
                data_print = []
                for r in res_lista.data:
                    al = r['alumnos']
                    data_print.append({
                        "id": r['id'],
                        "Apellido": al['apellido'].upper(),
                        "Nombre": al['nombre'],
                        "DNI": al['dni'],
                        "Curso": r['nombre_curso_materia']
                    })
                df = pd.DataFrame(data_print)
                
                for _, row in df.iterrows():
                    with st.container():
                        st.markdown(f'<div class="ficha-alumno"><b>{row["Apellido"]}, {row["Nombre"]}</b> - {row["Curso"]} (DNI: {row["DNI"]})</div>', unsafe_allow_html=True)
                        b1, b2, _ = st.columns([1,1,6])
                        if b1.button("✏️ Editar", key=f"ed_{row['id']}"): st.info("Edición")
                        if b2.button("🗑️ Borrar", key=f"del_{row['id']}"):
                            supabase.table("inscripciones").delete().eq("id", row['id']).execute()
                            st.rerun()
            else:
                st.info("No hay alumnos.")
