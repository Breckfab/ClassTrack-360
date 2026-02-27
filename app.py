import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v227", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO CLASSTRACK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

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
        components.html(f"""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{{hour12:false}})}},1000);</script>""", height=50)
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    # MOTOR DE DATOS (CURSOS DEL PROFESOR)
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (RECUPERACIÓN DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_227")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            
            # BUSQUEDA FORZADA DE TAREA PENDIENTE
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA ENTREGAR HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_227"):
                temas = st.text_area("Temas dictados hoy")
                n_tarea = st.text_area("Tarea para la próxima")
                vto = st.date_input("Vencimiento:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Guardado."); st.rerun()
                b2.form_submit_button("✏️ Editar")
                b3.form_submit_button("🗑️ Borrar")

    # --- TAB 3: NOTAS (LISTADO DE ALUMNOS FORZADO) ---
    with tabs[3]:
        st.subheader("📝 Notas")
        sub_n = st.radio("Acción:", ["Volcar Notas", "Consultar Notas"], horizontal=True)
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_227")
        
        if c_nt != "---":
            if sub_n == "Volcar Notas":
                # Traer alumnos inscritos en este curso específico
                res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                if not res_al_n.data: 
                    st.warning("No hay alumnos inscritos en este curso.")
                else:
                    for r in res_al_n.data:
                        al = r['alumnos']
                        with st.container():
                            st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                            with st.form(f"nt_form_{al['id']}"):
                                nota = st.number_input("Nota:", 0.0, 10.0, value=0.0, step=0.1)
                                nb1, nb2, nb3, _ = st.columns([1,1,1,5])
                                if nb1.form_submit_button("💾 Guardar"):
                                    supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_nt, "calificacion": nota, "fecha": str(datetime.date.today())}).execute()
                                    st.success("Nota guardada.")
                                nb2.form_submit_button("✏️ Editar")
                                nb3.form_submit_button("🗑️ Borrar")
            else:
                st.info("Buscando historial de notas...")

    # --- TAB 4: CURSOS (NUEVO CURSO CON DÍAS) ---
    with tabs[4]:
        sub_cu = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c_227"):
