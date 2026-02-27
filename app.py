import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. NÚCLEO ---
st.set_page_config(page_title="ClassTrack 360 v252", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- 2. ESTILO VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ACCESO Y SIDEBAR ---
if st.session_state.user is None:
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{hour12:false})},1000);</script>""", height=50)
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    # MOTOR DE DATOS
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (SENSOR RETROACTIVO) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_252")
            f_hoy = datetime.date.today()
            
            # SENSOR: Busca tareas cuya fecha de entrega sea HOY o ANTERIOR (pendientes)
            res_t = supabase.table("bitacora").select("tarea_proxima, fecha_tarea").eq("inscripcion_id", mapa_cursos[c_ag]).lte("fecha_tarea", str(f_hoy)).order("fecha_tarea", desc=True).limit(1).execute()
            
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">⚠️ TAREA PENDIENTE (Desde {res_t.data[0]["fecha_tarea"]}):<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_v252"):
                temas, n_tarea = st.text_area("Temas dictados hoy"), st.text_area("Tarea próxima")
                vto = st.date_input("Vencimiento:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Satisfactorio."); st.rerun()
                b2.form_submit_button("✏️ Editar"); b3.form_submit_button("🗑️ Borrar")

    # --- TAB 1: ALUMNOS (CONSULTA / NUEVO) ---
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Consulta", "Nuevo Alumno"], horizontal=True)
        if sub_al == "Nuevo Alumno":
            with st.form("new_al"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_sel = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    if ra.data:
                        supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                        st.success("Satisfactorio."); st.rerun()
        else:
            c_v = st.selectbox("Ver curso:", ["---"] + list(mapa_cursos.keys()))
            if c_v != "---":
                res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    al = r['alumnos'][0] if isinstance(r['alumnos'], list) else r['alumnos']
                    if al:
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        b1, b2, b3, _ = st.columns([1,1,1,5])
                        b1.button("✏️ Editar", key=f"eal_{r['id']}"); b2.button("🗑️ Borrar", key=f"dal_{r['id']}"); b3.button("💾 Guardar", key=f"sal_{r['id']}")

    # --- TAB 2: NOTAS ---
    with tabs[2]:
        st.subheader("📝 Notas")
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_252")
        if c_nt != "---":
            res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_al_n.data:
                al = r['alumnos'][0] if isinstance(r['alumnos'], list) else r['alumnos']
                if al:
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"
