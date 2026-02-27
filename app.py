import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v257", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- 2. ESTILO VISUAL (Protocolo de Alerta) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.25); border: 2px solid #ffc107; padding: 20px; border-radius: 12px; color: #ffc107; text-align: center; font-weight: 800; margin-bottom: 25px; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .stat-card { background: rgba(79, 172, 254, 0.1); border: 1px solid #4facfe; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ACCESO Y SIDEBAR ---
if st.session_state.user is None:
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            try:
                res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
                if res.data: st.session_state.user = res.data[0]; st.rerun()
            except: st.error("Error de conexión.")
else:
    u_data = st.session_state.user
    f_hoy = datetime.date.today()
    
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        st.write(f"📅 {f_hoy.strftime('%d/%m/%Y')}")
        components.html("""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{hour12:false})},1000);</script>""", height=50)
        
        # Contador Global Alumnos 2026
        res_total = supabase.table("inscripciones").select("id").eq("profesor_id", u_data['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
        st.markdown(f'<div class="stat-card">Total Alumnos 2026: <b>{len(res_total.data)}</b></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    # MOTOR DE DATOS
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (SENSOR DE TAREA PENDIENTE) ---
    with tabs[0]:
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso para iniciar clase:", list(mapa_cursos.keys()), key="ag_v257")
            
            # --- SENSOR DE ARRASTRE DE TAREA (Busca lo último anotado antes de hoy) ---
            res_t = supabase.table("bitacora").select("tarea_proxima, fecha").eq("inscripcion_id", mapa_cursos[c_ag]).lt("fecha", str(f_hoy)).order("fecha", desc=True).limit(1).execute()
            
            if res_t.data and res_t.data[0]['tarea_proxima']:
                st.markdown(f'''
                    <div class="tarea-alerta">
                        🔔 TAREA PENDIENTE DE LA CLASE ANTERIOR ({res_t.data[0]['fecha']})<br>
                        <div style="margin-top:10px; border-top:1px solid #ffc107; padding-top:10px; color:#fff; font-weight:400; font-size:1.1rem;">
                            {res_t.data[0]["tarea_proxima"]}
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("No hay tareas pendientes registradas de clases anteriores.")
            
            st.subheader("📝 Registro de la Clase Actual")
            with st.form("f_ag_v257"):
                temas = st.text_area("Contenido dictado hoy")
                n_tarea = st.text_area("Tarea para la próxima clase")
                vto = st.date_input("Fecha de entrega de esta nueva tarea:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar Datos de Hoy"):
                    supabase.table("bitacora").insert({
                        "inscripcion_id": mapa_cursos[c_ag], 
                        "fecha": str(f_hoy), 
                        "contenido_clase": temas, 
                        "tarea_proxima": n_tarea, 
                        "fecha_tarea": str(vto)
                    }).execute()
                    st.success("Satisfactorio."); st.rerun()
                b2.form_submit_button("✏️ Editar")
                b3.form_submit_button("🗑️ Borrar")
        else:
            st.warning("Debe crear un curso en la pestaña 'Cursos' primero.")

    # --- TAB 1: ALUMNOS (CONSULTA Y REGISTRO) ---
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Ver Lista", "Registrar Alumno Nuevo"], horizontal=True)
        if sub_al == "Registrar Alumno Nuevo":
            with st.form("new_al"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_sel = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    if ra.data:
                        supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                        st.success("Alumno Registrado."); st.rerun()
        else:
            c_v = st.selectbox("Filtrar por curso:", ["---"] + list(mapa_cursos.keys()))
            if c_v != "---":
                res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                st.info(f"Cantidad de alumnos: {len(res_al.data)}")
                for r in res_al.data:
                    al_raw = r.get('alumnos')
                    al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                    if al:
                        st.markdown(f'<div class="planilla-row">👤 {al.get("apellido", "").upper()}, {al.get("nombre", "")}</div>', unsafe_allow_html=True)

    # --- TAB 2: NOTAS ---
    with tabs[2]:
        st.subheader("📝 Notas")
        c_nt = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v257")
        if c_nt != "---":
            res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_al_n.data:
                al_raw = r.get('alumnos')
                al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                if al:
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al.get("apellido", "").upper()}, {al.get("nombre", "")}</div>', unsafe_allow_html=True)
                        with st.form(f"nt_{al['id']}"):
                            st.number_input("Calificación:", 0.0, 10.0, step=0.1)
                            st.form_submit_button("💾 Guardar Nota")

    # --- TAB 3: CURSOS ---
    with tabs[3]:
        sub_cu = st.radio("Acción:", ["Mis Cursos", "Crear Nuevo Curso"], horizontal=True)
        if sub_cu == "Crear Nuevo Curso":
            with st.form("new_c"):
                mat, hor = st.text_input("Materia"), st.text_input("Horario")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                if st.form_submit_button("💾 INSTALAR"):
                    info = f"{mat} ({', '.join(dias)}) | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Curso Instalado."); st.rerun()
        else:
            for n_c, i_c in mapa_cursos.items():
                res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", n_c).not_.is_("alumno_id", "null").execute()
                st.markdown(f'<div class="planilla-row">📖 {n_c} <br> <small style="color:#4facfe;">Alumnos: {res_count.count}</small></div>', unsafe_allow_html=True)
                cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                cb1.button("✏️ Editar", key=f"ec_{i_c}"); cb2.button("🗑️ Borrar", key=f"dc_{i_c}")
