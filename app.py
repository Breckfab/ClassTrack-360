import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v186", layout="wide")

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
    .empty-state { background: rgba(255, 255, 255, 0.05); padding: 40px; border-radius: 15px; text-align: center; border: 2px dashed #4facfe; margin-top: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
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
        u = st.text_input("Sede (ej: cambridge)").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: 
                st.session_state.user = res.data[0]
                st.rerun()
else:
    u_data = st.session_state.user
    # 1. BUSCAR SI EXISTEN CURSOS
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    cursos_existentes = res_c.data if res_c.data else []
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in cursos_existentes}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- PANTALLA PARA CUANDO NO HAY NADA ---
    def estado_vacio(mensaje):
        st.markdown(f"""<div class="empty-state"><h3>⚠️ {mensaje}</h3><p>Para usar esta pestaña, primero debés configurar un curso.</p></div>""", unsafe_allow_html=True)
        if st.button("Ir a Crear Curso ahora"):
            st.write("Cambiá a la pestaña 🏗️ Cursos arriba.")

    # --- TAB CURSOS (EL PRIMER PASO) ---
    with tabs[4]:
        st.subheader("🏗️ Configuración de Cursos")
        # Listado arriba
        if cursos_existentes:
            st.write("### Mis Cursos Activos")
            for cur in cursos_existentes:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 <b>{cur["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                    col1, col2, _ = st.columns([1,1,6])
                    if col1.button("✏️ Editar", key=f"ed_{cur['id']}"): st.toast("Editar habilitado")
                    if col2.button("🗑️ Borrar", key=f"del_{cur['id']}"):
                        supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                        st.rerun()
            st.divider()
        
        st.write("### Crear Nuevo Curso")
        with st.form("crear_curso_v186"):
            n = st.text_input("Nombre de la Materia (ej: Inglés Inicial)")
            d = st.text_input("Días y Horarios (ej: Lunes 18:00)")
            if st.form_submit_button("💾 GUARDAR CURSO"):
                if n and d:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{n} ({d})", "anio_lectivo": 2026}).execute()
                    st.success("Curso creado con éxito!"); time.sleep(0.5); st.rerun()

    # --- TAB ALUMNOS ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        if not cursos_existentes:
            estado_vacio("No hay cursos donde inscribir alumnos")
        else:
            with st.form("inscribir_v186"):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre")
                ape = c1.text_input("Apellido")
                dni = c2.text_input("DNI")
                cur_sel = st.selectbox("Inscribir en el curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 GUARDAR ALUMNO"):
                    if nom and ape:
                        res_al = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape, "dni": dni}).execute()
                        if res_al.data:
                            supabase.table("inscripciones").insert({
                                "alumno_id": res_al.data[0]['id'], "profesor_id": u_data['id'], 
                                "nombre_curso_materia": cur_sel, "anio_lectivo": 2026
                            }).execute()
                            st.success(f"✅ {ape} inscripto en {cur_sel}"); st.rerun()

    # --- TAB ASISTENCIA, NOTAS Y AGENDA ---
    # (Se activan solo si hay cursos y alumnos)
    for i, t in enumerate([tabs[0], tabs[2], tabs[3]]):
        with t:
            if not cursos_existentes:
                estado_vacio("Pestaña bloqueada")
            else:
                st.info("Seleccioná un curso para empezar a trabajar.")
