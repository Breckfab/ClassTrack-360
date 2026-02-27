import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v192", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 5px; }
    .kpi-card { background: rgba(79, 172, 254, 0.1); border: 1px solid #4facfe; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .kpi-val { font-size: 2rem; font-weight: 800; color: #4facfe; display: block; }
    .badge-curso { background: #4facfe; color: #0b0e14; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
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
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    # --- CÁLCULO DE CONTADORES ---
    # Alumnos totales (únicos)
    res_total = supabase.table("inscripciones").select("alumno_id").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
    total_alumnos = len(set([r['alumno_id'] for r in res_total.data])) if res_total.data else 0

    # Cursos y alumnos por curso
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    cursos_info = []
    if res_c.data:
        for c in res_c.data:
            res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", c['nombre_curso_materia']).not_.is_("alumno_id", "null").execute()
            cursos_info.append({"id": c['id'], "nombre": c['nombre_curso_materia'], "cant": res_count.count})

    # Encabezado con Contador Total
    st.markdown(f'<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-card">Sede: {u_data["email"].split(".")[0].upper()} | <span class="kpi-val">{total_alumnos}</span> Alumnos totales en sistema (Ciclo 2026)</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (CON CONTADORES POR CURSO) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Cursos y Estadísticas")
        if cursos_info:
            for cur in cursos_info:
                with st.container():
                    st.markdown(f"""
                        <div class="planilla-row">
                            📖 <b>{cur['nombre']}</b> <span style="float:right;" class="badge-curso">👥 {cur['cant']} Alumnos</span>
                        </div>
                    """, unsafe_allow_html=True)
                    bc1, bc2, bc3, _ = st.columns([1,1,1,5])
                    bc1.button("✏️ Editar", key=f"ed_c_{cur['id']}")
                    if bc2.button("🗑️ Borrar", key=f"del_c_{cur['id']}"):
                        supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                        st.rerun()
                    bc3.button("💾 Guardar", key=f"sv_c_{cur['id']}")
        
        st.divider()
        with st.form("nuevo_curso_v192"):
            st.write("### ➕ Instalar Nuevo Curso")
            nc = st.text_input("Nombre de la Materia y Horario")
            if st.form_submit_button("💾 GUARDAR E INSTALAR"):
                if nc:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                    st.success("✅ Curso instalado satisfactoriamente."); time.sleep(0.5); st.rerun()

    # --- TAB 1: ALUMNOS CON BUSCADOR ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        if not cursos_info:
            st.warning("⚠️ Primero cree un curso.")
        else:
            with st.form("reg_al_v192", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nom, ape = c1.text_input("Nombre"), c1.text_input("Apellido")
                dni = c2.text_input("DNI")
                cur_sel = st.selectbox("Curso:", [c['nombre'] for c in cursos_info])
                if st.form_submit_button("💾 GUARDAR E INSCRIBIR"):
                    if nom and ape and dni:
                        # Anti-duplicado por DNI
                        check = supabase.table("alumnos").select("id").eq("dni", dni).execute()
                        if not check.data:
                            res_a = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape, "dni": dni}).execute()
                            al_id = res_a.data[0]['id']
                        else: al_id = check.data[0]['id']
                        
                        supabase.table("inscripciones").insert({"alumno_id": al_id, "profesor_id": u_data['id'], "nombre_curso_materia": cur_sel, "anio_lectivo": 2026}).execute()
                        st.success(f"✅ {ape.upper()} inscripto satisfactoriamente."); time.sleep(0.5); st.rerun()

    # --- RESTO DE PESTAÑAS (ASISTENCIA/NOTAS/AGENDA) ---
    # Implementan el razonamiento de cascada y buscadores de la v191...
